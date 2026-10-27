"""Multi-sensor physical, geomorphic, hydrothermal-vent, and fold-proper fracture-mechanics features.

Strict Leakage Invariants (PARALLEL-RUN PROTOCOL Rules 2 & 4):
  1. Static features (36 channels) read ZERO fault-catalogue pixels, ZERO scored submission rasters,
     and explicitly strip ``dist_known_fault_px`` from ``gdr_wellspring_in_footprint.csv``.
  2. Fold-proper mechanical features (6 channels) are derived strictly from a fold's ``visible``
     fault mask (never touching withheld components) and use an exact binary bit-plane
     leave-self-component-out transform during training so training positives never see self-distance 0.
"""
from __future__ import annotations

import csv
import gc
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from skimage.morphology import skeletonize

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    # Group A: Piedmont Break-in-Slope, 10m 3DEP Geomorphometry, Chi-Disequilibrium & 1m LiDAR (13)
    "f01_det_elev_slope",
    "f02_piedmont_break_inflection",
    "f03_height_above_basin_floor",
    "f04_ridge_crest_convexity_deconf",
    "f05_lrm_openness_100m",
    "f06_topo10_slope_std",
    "f07_topo10_curv_prof",
    "f08_topo10_lineament_coh",
    "f09_chi_knick_step",
    "f10_chi_ksn",
    "f11_lidar_scarp_step",
    "f12_lidar_polarity_coh",
    "f13_road_safe_weight",
    # Group B: Hydrothermal Vent, Geothermometer, 2m Probe, Sinter/Tufa & Alteration Conduits (10)
    "f14_hydro_temp_near",
    "f15_hydro_geotherm_reservoir",
    "f16_probe_2m_f2mdab",
    "f17_paleo_sinter_tufa",
    "f18_mt_cond_surf",
    "f19_mt_cond_grad",
    "f20_rad_k_th_ratio",
    "f21_rad_alteration_edge",
    "f22_hydro_demag_trough",
    "f23_vent_conduit_bridge",
    # Group C: Potential-Field Vertical Attenuation, Cross-Gradient & Transtensional Geodesy (13)
    "f24_iso_grav_hg",
    "f25_iso_grav_vg",
    "f26_grav_tilt_grad",
    "f27_rtp_hp",
    "f28_tmi_hg",
    "f29_mag_tilt_edge",
    "f30_depth_to_base",
    "f31_basement_step_grad",
    "f32_gallardo_meju_coupling",
    "f33_multiphysics_strike_consensus",
    "f34_anderson_transtension_fav",
    "f35_geod_strain_2ndinv",
    "f36_geod_dilatation_seis",
    # Group S: Multi-Scale Spatial Context Pyramid (300 m & 900 m envelopes for sustained fault corridors) (12)
    "f37_ctx_slope_s3",
    "f38_ctx_slope_s9",
    "f39_ctx_break_s4",
    "f40_ctx_topo10_s3",
    "f41_ctx_topo10_s9",
    "f42_ctx_lidar_s4",
    "f43_ctx_chi_s5",
    "f44_ctx_grav_hg_s5",
    "f45_ctx_tmi_hg_s5",
    "f46_ctx_base_step_s6",
    "f47_ctx_mp_order_s4",
    "f48_ctx_demag_s5",
)

MECH_FEATURE_NAMES: tuple[str, ...] = (
    "m01_xcomp_dist",
    "m02_tip_strike_lobe",
    "m03_wingcrack_dilational",
    "m04_relay_stepover_bridge",
    "m05_regional_fault_density",
    "m06_hydro_orphan_conduit_boost",
)

ALL_FEATURE_NAMES: tuple[str, ...] = STATIC_FEATURE_NAMES + MECH_FEATURE_NAMES


def _clean_band(arr: np.ndarray, foot: np.ndarray) -> np.ndarray:
    a = arr.astype(np.float32, copy=False)
    valid = foot & np.isfinite(a) & (a > -1e30)
    med = float(np.median(a[valid])) if valid.any() else 0.0
    out = np.where(valid, a, np.float32(med))
    return out.astype(np.float32, copy=False)


def robust_z_fp(arr2d: np.ndarray, foot: np.ndarray, clip: float = 8.0) -> np.ndarray:
    """Return 1D float32 robust z-score strictly over ``foot`` pixels (minimal memory)."""
    v = arr2d[foot].astype(np.float32, copy=False)
    med = float(np.median(v))
    q25, q75 = np.percentile(v, [25.0, 75.0])
    iqr_sd = max(float(q75 - q25) / 1.349, 1e-6)
    z = (v - np.float32(med)) / np.float32(iqr_sd)
    np.clip(z, -clip, clip, out=z)
    return z


def robust_z_2d(arr2d: np.ndarray, foot: np.ndarray, clip: float = 8.0) -> np.ndarray:
    out = np.zeros(arr2d.shape, dtype=np.float32)
    out[foot] = robust_z_fp(arr2d, foot, clip=clip)
    return out


def _grad_f32(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Memory-lean central difference gradient in float32 (no float64 promotion)."""
    gy = np.empty_like(arr, dtype=np.float32)
    gx = np.empty_like(arr, dtype=np.float32)
    gy[1:-1, :] = 0.5 * (arr[2:, :] - arr[:-2, :])
    gy[0, :] = arr[1, :] - arr[0, :]
    gy[-1, :] = arr[-1, :] - arr[-2, :]
    gx[:, 1:-1] = 0.5 * (arr[:, 2:] - arr[:, :-2])
    gx[:, 0] = arr[:, 1] - arr[:, 0]
    gx[:, -1] = arr[:, -1] - arr[:, -2]
    return gy, gx


def _grad_mag_f32(arr: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    sm = ndi.gaussian_filter(arr.astype(np.float32, copy=False), sigma=sigma, mode="nearest")
    gy, gx = _grad_f32(sm)
    del sm
    np.hypot(gy, gx, out=gy)
    del gx
    return gy


def _structure_orientation(field: np.ndarray, sigma: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    sm = ndi.gaussian_filter(field.astype(np.float32, copy=False), sigma=sigma, mode="nearest")
    gy, gx = _grad_f32(sm)
    del sm
    jxx = ndi.gaussian_filter(gx * gx, sigma=sigma * 1.5, mode="nearest")
    jyy = ndi.gaussian_filter(gy * gy, sigma=sigma * 1.5, mode="nearest")
    jxy = ndi.gaussian_filter(gx * gy, sigma=sigma * 1.5, mode="nearest")
    del gx, gy
    tr = jxx + jyy + np.float32(1e-12)
    diff = (jxx - jyy) * np.float32(0.5)
    coh = np.hypot(diff, jxy) / tr
    strike_theta = np.float32(0.5) * np.arctan2(np.float32(2.0) * jxy, (jxx - jyy) + np.float32(1e-12)) + np.float32(0.5 * np.pi)
    return strike_theta.astype(np.float32, copy=False), coh.astype(np.float32, copy=False)


def _shift2d_add(acc: np.ndarray, src: np.ndarray, sy: int, sx: int, wt: float) -> None:
    """In-place weighted shifted accumulation without allocating full-array copies."""
    H, W = src.shape
    y0_d, y1_d = max(0, sy), min(H, H + sy)
    y0_s, y1_s = max(0, -sy), min(H, H - sy)
    x0_d, x1_d = max(0, sx), min(W, W + sx)
    x0_s, x1_s = max(0, -sx), min(W, W - sx)
    if y1_d > y0_d and x1_d > x0_d:
        acc[y0_d:y1_d, x0_d:x1_d] += np.float32(wt) * src[y0_s:y1_s, x0_s:x1_s]


def _anisotropic_smooth(grid_impulses: np.ndarray, sig_along: float, sig_across: float, az_deg: float = 18.0) -> np.ndarray:
    rad = np.deg2rad(az_deg)
    dy, dx = -np.cos(rad), np.sin(rad)
    base = ndi.gaussian_filter(grid_impulses.astype(np.float32, copy=False), sigma=sig_across, mode="constant")
    acc = np.zeros_like(base, dtype=np.float32)
    wsum = 0.0
    step_scale = max(sig_along * 0.55, 1.0)
    for k in (-2.0, -1.0, 0.0, 1.0, 2.0):
        wt = float(np.exp(-0.5 * (k * 0.7) ** 2))
        sy = int(round(k * step_scale * dy))
        sx = int(round(k * step_scale * dx))
        _shift2d_add(acc, base, sy, sx, wt)
        wsum += wt
    acc /= np.float32(wsum)
    return acc


def _populate_group_a(mm: np.memmap, data_dir: Path, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(data_dir / "training_features.tif") as ds:
        det_elev = _clean_band(ds.read(12), foot)
        det_slope = _clean_band(ds.read(19), foot)

    mm[:, 0] = robust_z_fp(det_slope, foot)
    mm[:, 1] = robust_z_fp(_grad_mag_f32(det_slope, sigma=1.4), foot)

    # Height Above Local Basin Floor (3.5 km window): isolates the range-front piedmont fault zone
    # (20-260 m above valley floor) from both central playas (<10 m) and high mountain crests (>500 m).
    valley_floor = ndi.minimum_filter(ndi.gaussian_filter(det_elev, sigma=2.0, mode="nearest"), size=35, mode="nearest")
    hanvf = np.log1p(np.maximum(det_elev - valley_floor, np.float32(0.0)))
    mm[:, 2] = robust_z_fp(hanvf, foot)
    del valley_floor, hanvf

    elev_sm2 = ndi.gaussian_filter(det_elev, sigma=2.0, mode="nearest")
    ridge_convex = -ndi.laplace(elev_sm2)
    mm[:, 3] = robust_z_fp(ridge_convex, foot)
    del elev_sm2, ridge_convex

    lrm_100 = np.abs(
        ndi.gaussian_filter(det_elev, 1.0, mode="nearest")
        - ndi.gaussian_filter(det_elev, 6.0, mode="nearest")
    )
    mm[:, 4] = robust_z_fp(lrm_100, foot)
    del lrm_100, det_elev

    with rasterio.open(data_dir / "external" / "topo_10m_derived_100m_u8.tif") as ds:
        t10_slope_std = ds.read(4).astype(np.float32)
        mm[:, 5] = robust_z_fp(t10_slope_std, foot)
        t10_curv_prof = ds.read(6).astype(np.float32)
        mm[:, 6] = robust_z_fp(t10_curv_prof, foot)
        del t10_curv_prof
        t10_coh = (ds.read(7).astype(np.float32) * ds.read(8).astype(np.float32)) / np.float32(65025.0)
        mm[:, 7] = robust_z_fp(t10_coh, foot)
        del t10_coh

    with rasterio.open(data_dir / "external" / "dem10_chi_100m_i16.tif") as ds:
        chi_step = np.log1p(np.maximum(ds.read(1).astype(np.float32), np.float32(0.0)))
        mm[:, 8] = robust_z_fp(chi_step, foot)
        del chi_step
        chi_ksn = np.log1p(np.maximum(ds.read(3).astype(np.float32), np.float32(0.0)))
        mm[:, 9] = robust_z_fp(chi_ksn, foot)
        del chi_ksn

    with rasterio.open(data_dir / "external" / "lidar_scarp_features_u8.tif") as ds:
        lid_ex = ds.read(1).astype(np.float32)
        lid_step = ds.read(3).astype(np.float32)
        lid_down = ds.read(6).astype(np.float32)
        lid_up = ds.read(7).astype(np.float32)
        lid_coh = ds.read(10).astype(np.float32) / np.float32(255.0)
        lid_valid = ds.read(12) > 0

    scarp_raw = 0.5 * lid_ex + 0.5 * lid_step
    mm[:, 10] = robust_z_fp(_clean_band(np.where(lid_valid, scarp_raw, np.nan), foot), foot)
    pol_raw = (np.abs(lid_down - lid_up) / (lid_down + lid_up + np.float32(5.0))) * lid_coh * scarp_raw
    mm[:, 11] = robust_z_fp(_clean_band(np.where(lid_valid, pol_raw, np.nan), foot), foot)
    del lid_ex, lid_step, lid_down, lid_up, lid_coh, lid_valid, scarp_raw, pol_raw

    with rasterio.open(data_dir / "external" / "tiger_road_distance_m.tif") as ds:
        road_d = _clean_band(ds.read(1), foot)
    mm[:, 12] = robust_z_fp(np.clip(road_d / np.float32(250.0), np.float32(0.0), np.float32(1.0)), foot)
    del road_d
    mm.flush()
    gc.collect()
    return det_slope, t10_slope_std


def _populate_group_b(mm: np.memmap, data_dir: Path, foot: np.ndarray) -> np.ndarray:
    H, W = foot.shape
    imp_temp = np.zeros((H, W), dtype=np.float32)
    imp_geoth = np.zeros((H, W), dtype=np.float32)

    # STRICT INVARIANT: Never read column `dist_known_fault_px`!
    ws_csv = data_dir / "external" / "gdr_wellspring_in_footprint.csv"
    with ws_csv.open("r", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError, TypeError):
                continue
            if not (0 <= r < H and 0 <= c < W):
                continue
            raw_t = row.get("temp_c")
            if raw_t not in (None, "", "NULL", "NaN"):
                try:
                    tv = max(0.0, float(raw_t) - 20.0)
                    if tv > imp_temp[r, c]:
                        imp_temp[r, c] = min(tv, 180.0)
                except ValueError:
                    pass
            gt_max = 0.0
            for gk in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                raw_g = row.get(gk)
                if raw_g not in (None, "", "NULL", "NaN"):
                    try:
                        gv = float(raw_g)
                        if np.isfinite(gv) and gv < 400.0:
                            gt_max = max(gt_max, max(0.0, gv - 75.0))
                    except ValueError:
                        pass
            if gt_max > imp_geoth[r, c]:
                imp_geoth[r, c] = min(gt_max, 250.0)

    hydro_temp_near = _anisotropic_smooth(np.log1p(imp_temp), sig_along=14.0, sig_across=7.5, az_deg=18.0)
    hydro_geotherm = _anisotropic_smooth(np.log1p(imp_geoth), sig_along=22.0, sig_across=12.0, az_deg=18.0)
    del imp_temp, imp_geoth
    mm[:, 13] = robust_z_fp(hydro_temp_near, foot)
    mm[:, 14] = robust_z_fp(hydro_geotherm, foot)

    with rasterio.open(data_dir / "external" / "derived_gdr_2m_probes_100m_u8.tif") as ds:
        p2m_raw = ds.read(1).astype(np.float32)
    probe_2m = 0.6 * ndi.gaussian_filter(p2m_raw, 4.0, mode="constant") + 0.4 * ndi.gaussian_filter(p2m_raw, 12.0, mode="constant")
    del p2m_raw
    mm[:, 15] = robust_z_fp(probe_2m, foot)

    with rasterio.open(data_dir / "external" / "derived_gdr_paleo_100m_u8.tif") as ds:
        pal_raw = ds.read(1).astype(np.float32)
    vv_csv = data_dir / "external" / "gdr_volcanic_vents_in_footprint.csv"
    if vv_csv.exists():
        with vv_csv.open("r", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                try:
                    rr, cc = int(float(row["row"])), int(float(row["col"]))
                    if 0 <= rr < H and 0 <= cc < W:
                        pal_raw[rr, cc] = max(pal_raw[rr, cc], 200.0)
                except (KeyError, ValueError, TypeError):
                    pass
    paleo_vent = 0.6 * ndi.gaussian_filter(pal_raw, 5.0, mode="constant") + 0.4 * ndi.gaussian_filter(pal_raw, 16.0, mode="constant")
    del pal_raw
    mm[:, 16] = robust_z_fp(paleo_vent, foot)

    vent_seed = (
        np.maximum(robust_z_2d(hydro_temp_near, foot), np.float32(0.0))
        + np.float32(0.8) * np.maximum(robust_z_2d(hydro_geotherm, foot), np.float32(0.0))
        + np.float32(0.9) * np.maximum(robust_z_2d(probe_2m, foot), np.float32(0.0))
        + np.float32(0.7) * np.maximum(robust_z_2d(paleo_vent, foot), np.float32(0.0))
    )
    del hydro_temp_near, hydro_geotherm, probe_2m, paleo_vent

    with rasterio.open(data_dir / "training_features.tif") as ds:
        rtp = _clean_band(ds.read(2), foot)
        cond_surf = _clean_band(ds.read(17), foot)
        iso_hg = _clean_band(ds.read(18), foot)

    mm[:, 17] = robust_z_fp(cond_surf, foot)
    mm[:, 18] = robust_z_fp(_grad_mag_f32(cond_surf, sigma=2.0), foot)

    with rasterio.open(data_dir / "external" / "geodawn_rad_u8.tif") as ds:
        rad_k = ds.read(1).astype(np.float32)
        rad_th = ds.read(2).astype(np.float32)
        rad_valid = ds.read(4) > 0
    with rasterio.open(data_dir / "external" / "geodawn_extensions_u8.tif") as ds:
        ext_uth = ds.read(3).astype(np.float32)
        tmi_up150 = ds.read(4).astype(np.float32)

    k_enr = _clean_band(np.where(rad_valid, rad_k - np.float32(0.68) * rad_th, np.nan), foot)
    mm[:, 19] = robust_z_fp(k_enr, foot)
    del rad_th, k_enr

    rad_edge = _grad_mag_f32(_clean_band(np.where(rad_valid, rad_k, np.nan), foot), sigma=1.5) + np.float32(0.7) * _grad_mag_f32(
        _clean_band(np.where(rad_valid, ext_uth, np.nan), foot), sigma=1.5
    )
    mm[:, 20] = robust_z_fp(rad_edge, foot)
    del rad_k, ext_uth, rad_valid, rad_edge

    rtp_hp = rtp - ndi.gaussian_filter(rtp, 8.0, mode="nearest")
    tmi_up_z = robust_z_2d(_clean_band(np.where(tmi_up150 > 0, tmi_up150, np.nan), foot), foot)
    del tmi_up150
    rtp_hp_z = robust_z_2d(rtp_hp, foot)
    del rtp_hp, rtp
    grav_edge_pos = np.maximum(robust_z_2d(iso_hg, foot), np.float32(0.0))
    del iso_hg
    demag_trough = np.maximum(tmi_up_z - rtp_hp_z, np.float32(0.0)) * np.sqrt(grav_edge_pos + np.float32(0.15))
    del tmi_up_z, rtp_hp_z, grav_edge_pos
    mm[:, 21] = robust_z_fp(demag_trough, foot)
    del demag_trough

    vent_bridge = np.float32(0.65) * _anisotropic_smooth(vent_seed, sig_along=26.0, sig_across=6.0, az_deg=18.0) + np.float32(0.35) * _anisotropic_smooth(
        vent_seed, sig_along=24.0, sig_across=6.0, az_deg=142.0
    )
    del vent_seed
    mm[:, 22] = robust_z_fp(vent_bridge, foot)
    del vent_bridge
    mm.flush()
    gc.collect()
    return cond_surf


def _populate_group_c(
    mm: np.memmap,
    data_dir: Path,
    foot: np.ndarray,
    det_slope: np.ndarray,
    t10_slope_std: np.ndarray,
    cond_surf: np.ndarray,
) -> None:
    H, W = foot.shape
    with rasterio.open(data_dir / "training_features.tif") as ds:
        rtp = _clean_band(ds.read(2), foot)
        tmi_hg = _clean_band(ds.read(3), foot)
        geod_2nd = _clean_band(ds.read(4), foot)
        tc = _clean_band(ds.read(6), foot)
        geod_shear = _clean_band(ds.read(7), foot)
        geod_dil = _clean_band(ds.read(8), foot)
        iso_vg = _clean_band(ds.read(11), foot)
        iso_grav = _clean_band(ds.read(13), foot)
        depth_base = _clean_band(ds.read(15), foot)
        ieq = _clean_band(ds.read(16), foot)
        iso_hg = _clean_band(ds.read(18), foot)

    mm[:, 23] = robust_z_fp(iso_hg, foot)
    mm[:, 24] = robust_z_fp(iso_vg, foot)

    grav_tilt = np.arctan2(iso_vg, np.maximum(iso_hg, np.float32(1e-5)))
    mm[:, 25] = robust_z_fp(_grad_mag_f32(grav_tilt, sigma=1.5), foot)
    del grav_tilt, iso_hg, iso_vg

    rtp_hp = rtp - ndi.gaussian_filter(rtp, 8.0, mode="nearest")
    mm[:, 26] = robust_z_fp(rtp_hp, foot)
    del rtp_hp
    mm[:, 27] = robust_z_fp(tmi_hg, foot)
    del tmi_hg

    tc_sd = float(np.std(tc[foot])) + 1e-6
    mag_tilt_edge = _grad_mag_f32(tc, sigma=1.5) * np.exp(-np.abs(tc) / np.float32(tc_sd))
    mm[:, 28] = robust_z_fp(mag_tilt_edge, foot)
    del tc, mag_tilt_edge

    mm[:, 29] = robust_z_fp(depth_base, foot)
    mm[:, 30] = robust_z_fp(_grad_mag_f32(depth_base, sigma=2.0), foot)
    del depth_base

    ggy, ggx = _grad_f32(ndi.gaussian_filter(iso_grav, 2.0, mode="nearest"))
    mgy, mgx = _grad_f32(ndi.gaussian_filter(rtp, 2.0, mode="nearest"))
    g_mag = np.hypot(ggy, ggx)
    m_mag = np.hypot(mgy, mgx)
    cross_sin = np.abs(ggx * mgy - ggy * mgx) / (g_mag * m_mag + np.float32(1e-6))
    gm_coupling = (np.float32(1.0) - cross_sin) * np.sqrt(g_mag * m_mag + np.float32(1e-8))
    mm[:, 31] = robust_z_fp(gm_coupling, foot)
    del ggy, ggx, mgy, mgx, g_mag, m_mag, cross_sin, gm_coupling

    cos2_sum = np.zeros((H, W), dtype=np.float32)
    sin2_sum = np.zeros((H, W), dtype=np.float32)
    w_tot = np.full((H, W), 1e-6, dtype=np.float32)
    for fld in (det_slope, t10_slope_std, iso_grav, rtp, cond_surf):
        st_th, st_coh = _structure_orientation(fld, sigma=2.0)
        cos2_sum += st_coh * np.cos(np.float32(2.0) * st_th)
        sin2_sum += st_coh * np.sin(np.float32(2.0) * st_th)
        w_tot += st_coh
        del st_th, st_coh
    del iso_grav, rtp

    mp_order = np.hypot(cos2_sum, sin2_sum) / w_tot
    mm[:, 32] = robust_z_fp(mp_order, foot)

    dom_th = np.float32(0.5) * np.arctan2(sin2_sum, cos2_sum)
    del cos2_sum, sin2_sum, w_tot
    th_nne = np.float32(np.deg2rad(18.0 - 90.0))
    th_nw = np.float32(np.deg2rad(142.0 - 90.0))
    anderson_fav = mp_order * (np.cos(dom_th - th_nne) ** 2 + np.float32(0.70) * np.cos(dom_th - th_nw) ** 2)
    mm[:, 33] = robust_z_fp(anderson_fav, foot)
    del mp_order, dom_th, anderson_fav

    mm[:, 34] = np.float32(0.55) * robust_z_fp(geod_2nd, foot) + np.float32(0.45) * robust_z_fp(geod_shear, foot)
    mm[:, 35] = np.float32(0.65) * robust_z_fp(geod_dil, foot) + np.float32(0.35) * robust_z_fp(ieq, foot)
    mm.flush()
    gc.collect()


def _populate_group_s(mm: np.memmap, foot: np.ndarray) -> None:
    """Populate 12 multi-scale spatial context channels (300 m - 900 m sustained corridor context)."""
    specs = (
        (36, 0, 3.0),   # f37_ctx_slope_s3
        (37, 0, 9.0),   # f38_ctx_slope_s9
        (38, 1, 4.0),   # f39_ctx_break_s4
        (39, 5, 3.0),   # f40_ctx_topo10_s3
        (40, 5, 9.0),   # f41_ctx_topo10_s9
        (41, 10, 4.0),  # f42_ctx_lidar_s4
        (42, 8, 5.0),   # f43_ctx_chi_s5
        (43, 23, 5.0),  # f44_ctx_grav_hg_s5
        (44, 27, 5.0),  # f45_ctx_tmi_hg_s5
        (45, 30, 6.0),  # f46_ctx_base_step_s6
        (46, 32, 4.0),  # f47_ctx_mp_order_s4
        (47, 21, 5.0),  # f48_ctx_demag_s5
    )
    buf2d = np.zeros(foot.shape, dtype=np.float32)
    for dst_col, src_col, sig in specs:
        buf2d.fill(0.0)
        buf2d[foot] = np.asarray(mm[:, src_col], dtype=np.float32)
        sm = ndi.gaussian_filter(buf2d, sigma=sig, mode="nearest")
        mm[:, dst_col] = robust_z_fp(sm, foot)
        del sm
    del buf2d
    mm.flush()
    gc.collect()


def build_static_feature_memmap(
    data_dir: Path,
    cache_dir: Path,
    force: bool = False,
) -> tuple[np.memmap, np.ndarray, np.ndarray, dict]:
    """Build or load the 36-channel leak-free physical & hydrothermal feature stack on footprint pixels."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    mmap_path = cache_dir / "static_features_fp_v1.mmap"
    meta_path = cache_dir / "static_features_fp_v1.json"

    with rasterio.open(data_dir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(data_dir / "existing_faults.tif") as ds:
        cat = (ds.read(1) == 1) & foot

    n_fp = int(foot.sum())
    n_feat = len(STATIC_FEATURE_NAMES)

    if not force and mmap_path.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("n_fp") == n_fp and meta.get("feature_names") == list(STATIC_FEATURE_NAMES):
            mm = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_feat))
            return mm, foot, cat, meta

    mm = np.memmap(mmap_path, dtype=np.float32, mode="w+", shape=(n_fp, n_feat))
    det_slope, t10_slope_std = _populate_group_a(mm, data_dir, foot)
    cond_surf = _populate_group_b(mm, data_dir, foot)
    _populate_group_c(mm, data_dir, foot, det_slope, t10_slope_std, cond_surf)
    del det_slope, t10_slope_std, cond_surf
    _populate_group_s(mm, foot)
    del mm
    gc.collect()

    H, W = foot.shape
    meta = {
        "schema_version": 1,
        "n_fp": n_fp,
        "grid_shape": [H, W],
        "n_static_features": n_feat,
        "feature_names": list(STATIC_FEATURE_NAMES),
        "catalogue_inputs_used": 0,
        "dist_known_fault_px_stripped": True,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    mm_ro = np.memmap(mmap_path, dtype=np.float32, mode="r", shape=(n_fp, n_feat))
    return mm_ro, foot, cat, meta


def _exact_cross_component_distance(comp: np.ndarray, max_comp: int, nearest_id: np.ndarray) -> np.ndarray:
    """Exact distance from every pixel to the nearest visible component OTHER than ``nearest_id``."""
    if max_comp <= 1:
        return np.full(comp.shape, 60.0, dtype=np.float32)
    n_bits = int(max_comp).bit_length()
    d_other = np.full(comp.shape, 1e6, dtype=np.float32)
    pos = comp > 0
    for b in range(n_bits):
        bit_mask = ((comp >> b) & 1) == 1
        bit_is_1 = pos & bit_mask
        bit_is_0 = pos & (~bit_mask)
        del bit_mask
        d_to_1 = ndi.distance_transform_edt(~bit_is_1).astype(np.float32) if bit_is_1.any() else None
        del bit_is_1
        d_to_0 = ndi.distance_transform_edt(~bit_is_0).astype(np.float32) if bit_is_0.any() else None
        del bit_is_0
        near_bit_1 = ((nearest_id >> b) & 1) == 1
        if d_to_0 is not None and d_to_1 is not None:
            cand = np.where(near_bit_1, d_to_0, d_to_1)
        elif d_to_0 is not None:
            cand = np.where(near_bit_1, d_to_0, np.float32(1e6))
        elif d_to_1 is not None:
            cand = np.where(near_bit_1, np.float32(1e6), d_to_1)
        else:
            continue
        np.minimum(d_other, cand, out=d_other)
        del d_to_1, d_to_0, cand, near_bit_1
    return d_other


def extract_visible_mechanics(
    visible_mask: np.ndarray,
    foot: np.ndarray,
    hydro_composite_fp: np.ndarray,
) -> np.ndarray:
    """Compute 6 fold-proper mechanical transfer features strictly from ``visible_mask``."""
    H, W = foot.shape
    vis = np.asarray(visible_mask, dtype=bool) & foot
    comp, n_comp = ndi.label(vis, np.ones((3, 3), dtype=bool))
    comp = comp.astype(np.int32, copy=False)
    d_self_f64, idx_near = ndi.distance_transform_edt(~vis, return_indices=True)
    d_self = d_self_f64.astype(np.float32)
    del d_self_f64
    nearest_comp = comp[idx_near[0], idx_near[1]]
    del idx_near

    d_other = _exact_cross_component_distance(comp, n_comp, nearest_comp)
    alpha_blend = np.clip((d_self - np.float32(2.0)) / np.float32(2.5), np.float32(0.0), np.float32(1.0))
    eff_dist = alpha_blend * d_self + (np.float32(1.0) - alpha_blend) * d_other
    # Clamp below 4.5 px so training positives never create a degenerate 2-3 px collar spike!
    eff_dist_clamped = np.maximum(eff_dist, np.float32(4.5))
    del d_self, d_other

    out_fp = np.empty((int(foot.sum()), len(MECH_FEATURE_NAMES)), dtype=np.float32)
    m01_dist = -np.log1p(np.minimum(eff_dist_clamped, np.float32(60.0)))
    out_fp[:, 0] = robust_z_fp(m01_dist, foot)
    del m01_dist, eff_dist_clamped

    # Skeletonize visible traces & locate degree-1 fault tips + outward strike tangent
    skel = skeletonize(vis)
    nbr_count = ndi.convolve(
        skel.astype(np.int16),
        np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16),
        mode="constant",
    )
    tips = skel & (nbr_count == 1)
    del nbr_count
    tip_y, tip_x = np.nonzero(tips)
    del tips
    tip_comp = comp[tip_y, tip_x]

    # Compute local centroid offset in tiny 9x9 window around each tip (zero full-grid coordinate arrays!)
    out_dy = np.zeros(len(tip_y), dtype=np.float32)
    out_dx = np.zeros(len(tip_x), dtype=np.float32)
    for k_idx, (ty, tx) in enumerate(zip(tip_y, tip_x)):
        y0, y1 = max(0, int(ty) - 4), min(H, int(ty) + 5)
        x0, x1 = max(0, int(tx) - 4), min(W, int(tx) + 5)
        sub = skel[y0:y1, x0:x1]
        sy, sx = np.nonzero(sub)
        if len(sy) > 1:
            vy = float(ty - y0) - float(sy.mean())
            vx = float(tx - x0) - float(sx.mean())
            nrm = float(np.hypot(vy, vx)) + 1e-6
            out_dy[k_idx] = vy / nrm
            out_dx[k_idx] = vx / nrm
    del skel

    best_strike_val = np.zeros((H, W), dtype=np.float32)
    second_strike_val = np.zeros((H, W), dtype=np.float32)
    best_strike_cid = np.zeros((H, W), dtype=np.int32)

    best_wing_val = np.zeros((H, W), dtype=np.float32)
    second_wing_val = np.zeros((H, W), dtype=np.float32)
    best_wing_cid = np.zeros((H, W), dtype=np.int32)

    R_PATCH = 18
    py, px = np.mgrid[-R_PATCH : R_PATCH + 1, -R_PATCH : R_PATCH + 1].astype(np.float32)
    pr = np.hypot(py, px) + np.float32(1e-6)
    radial_mask = (pr >= 1.0) & (pr <= R_PATCH)
    decay_strike = (np.exp(-pr / np.float32(9.5)) * radial_mask).astype(np.float32)
    decay_wing = (np.exp(-pr / np.float32(8.0)) * radial_mask).astype(np.float32)

    for ty, tx, dy, dx, cid in zip(tip_y, tip_x, out_dy, out_dx, tip_comp):
        if dy == 0.0 and dx == 0.0:
            continue
        ty_i, tx_i = int(ty), int(tx)
        cid_i = int(cid)
        y0, y1 = max(0, ty_i - R_PATCH), min(H, ty_i + R_PATCH + 1)
        x0, x1 = max(0, tx_i - R_PATCH), min(W, tx_i + R_PATCH + 1)
        ly0, ly1 = y0 - (ty_i - R_PATCH), R_PATCH * 2 + 1 - ((ty_i + R_PATCH + 1) - y1)
        lx0, lx1 = x0 - (tx_i - R_PATCH), R_PATCH * 2 + 1 - ((tx_i + R_PATCH + 1) - x1)

        sub_py = py[ly0:ly1, lx0:lx1]
        sub_px = px[ly0:ly1, lx0:lx1]
        sub_pr = pr[ly0:ly1, lx0:lx1]
        cos_ang = (sub_py * dy + sub_px * dx) / sub_pr
        fwd = np.maximum(cos_ang, np.float32(0.0))
        strike_patch = (fwd ** 4) * decay_strike[ly0:ly1, lx0:lx1]
        sin_ang = np.abs(sub_py * dx - sub_px * dy) / sub_pr
        wing_patch = (np.float32(4.0) * (fwd ** 2) * (sin_ang ** 2)) * decay_wing[ly0:ly1, lx0:lx1]

        # Exact top-2 distinct component tracker for strike lobe
        b_val = best_strike_val[y0:y1, x0:x1]
        s_val = second_strike_val[y0:y1, x0:x1]
        b_cid = best_strike_cid[y0:y1, x0:x1]
        same_c = b_cid == cid_i
        b_val[same_c] = np.maximum(b_val[same_c], strike_patch[same_c])
        beat_best = (~same_c) & (strike_patch > b_val)
        if beat_best.any():
            s_val[beat_best] = b_val[beat_best]
            b_val[beat_best] = strike_patch[beat_best]
            b_cid[beat_best] = cid_i
        beat_sec = (~same_c) & (~beat_best) & (strike_patch > s_val)
        if beat_sec.any():
            s_val[beat_sec] = strike_patch[beat_sec]

        # Exact top-2 distinct component tracker for wing-crack lobe
        bw_val = best_wing_val[y0:y1, x0:x1]
        sw_val = second_wing_val[y0:y1, x0:x1]
        bw_cid = best_wing_cid[y0:y1, x0:x1]
        same_cw = bw_cid == cid_i
        bw_val[same_cw] = np.maximum(bw_val[same_cw], wing_patch[same_cw])
        beat_bw = (~same_cw) & (wing_patch > bw_val)
        if beat_bw.any():
            sw_val[beat_bw] = bw_val[beat_bw]
            bw_val[beat_bw] = wing_patch[beat_bw]
            bw_cid[beat_bw] = cid_i
        beat_sw = (~same_cw) & (~beat_bw) & (wing_patch > sw_val)
        if beat_sw.any():
            sw_val[beat_sw] = wing_patch[beat_sw]

    tip_other = np.where(best_strike_cid == nearest_comp, second_strike_val, best_strike_val)
    m02 = alpha_blend * best_strike_val + (np.float32(1.0) - alpha_blend) * tip_other
    out_fp[:, 1] = robust_z_fp(m02, foot)
    del tip_other, m02, best_strike_cid

    wing_other = np.where(best_wing_cid == nearest_comp, second_wing_val, best_wing_val)
    m03 = alpha_blend * best_wing_val + (np.float32(1.0) - alpha_blend) * wing_other
    out_fp[:, 2] = robust_z_fp(m03, foot)
    del wing_other, m03, best_wing_cid

    # Exact two-component en-echelon relay / step-over bridge (nonzero iff >=2 distinct components interact)
    relay_bridge = np.sqrt(best_strike_val * second_strike_val + np.float32(0.5) * best_wing_val * second_wing_val)
    out_fp[:, 3] = robust_z_fp(relay_bridge, foot)
    del best_strike_val, second_strike_val, best_wing_val, second_wing_val, relay_bridge

    # 4-bucket leave-self-component-out regional structural-belt density
    dens_buckets = []
    for rem in range(4):
        mask_r = ((comp > 0) & ((comp & 3) == rem)).astype(np.float32)
        dens_buckets.append(ndi.gaussian_filter(mask_r, sigma=28.0, mode="constant"))
        del mask_r
    del comp
    dens_all = dens_buckets[0] + dens_buckets[1] + dens_buckets[2] + dens_buckets[3]
    near_rem = nearest_comp & 3
    del nearest_comp
    dens_self_bucket = np.choose(near_rem, dens_buckets)
    del dens_buckets, near_rem
    dens_other = (dens_all - dens_self_bucket) * np.float32(4.0 / 3.0)
    del dens_self_bucket
    m05 = alpha_blend * dens_all + (np.float32(1.0) - alpha_blend) * dens_other
    out_fp[:, 4] = robust_z_fp(m05, foot)
    del dens_all, dens_other, m05, alpha_blend

    hydro_2d = np.zeros((H, W), dtype=np.float32)
    hydro_2d[foot] = np.maximum(hydro_composite_fp, np.float32(0.0))
    orphan_factor = np.clip(eff_dist / np.float32(15.0), np.float32(0.15), np.float32(1.5))
    del eff_dist
    m06 = hydro_2d * orphan_factor
    out_fp[:, 5] = robust_z_fp(m06, foot)
    del hydro_2d, orphan_factor, m06
    gc.collect()
    return out_fp
