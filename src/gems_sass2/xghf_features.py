"""SASS2-XGHF 48-Channel Multi-Physics & Hydrothermal Conduit Feature Stack (Low-RSS Channel-First Memmap).

Stored as channel-first `(48, 3730, 3292)` `float16` memmap so each channel write/read is a
contiguous 24.5 MB slice (`< 550 MB` peak RSS on 3.8 GiB zero-swap machines).

100% label-free (NEVER reads `labels.tif` or `derived_sgmc_faults_100m_u8.tif`; explicitly
rejects `dist_known_fault_px` from GDR CSVs — fixing `IR-TEMPLATE-CSV-LEAK-03`) and 100%
built from verified official USGS & DOE GDR sources (ZERO synthetic `randn` fields!).
"""

from __future__ import annotations

import csv
import gc
import io
import json
import struct
import zipfile
from pathlib import Path

import numpy as np
import pyproj
import rasterio
from scipy import ndimage
from sklearn.metrics import roc_auc_score

from .paths import EXPECTED_SHAPE, NODATA_SENTINEL_F32

OFFICIAL_19_NAMES = [
    "b01_mag_anom",
    "b02_rtp",
    "b03_tmi_hg",
    "b04_geod_2ndinv",
    "b05_iso_grav_slope",
    "b06_tc",
    "b07_geod_shearrate",
    "b08_geod_dilaterate",
    "b09_tmi_vg",
    "b10_deq_n100a15",
    "b11_iso_grav_vg",
    "b12_det_elev",
    "b13_iso_grav_anom",
    "b14_tmi",
    "b15_depth_to_base",
    "b16_ieq_n100a15",
    "b17_cond_surf",
    "b18_iso_grav_hg",
    "b19_det_elev_slope",
]

STRUCTURAL_15_NAMES = [
    "s20_dem_ridge_s1",
    "s21_dem_ridge_s2",
    "s22_dem_ridge_s35",
    "s23_dem_tophat5",
    "s24_dem_relief5",
    "s25_dem_st_coh",
    "s26_dem_strike_cos2",
    "s27_dem_strike_sin2",
    "s28_lidar_ex_max",
    "s29_lidar_step_max",
    "s30_lidar_asymmetry",
    "s31_lidar_coh100",
    "s32_lidar_valid",
    "s33_rad_thk_ratio",
    "s34_mag_up150_resid",
]

XGHF_14_NAMES = [
    "xghf35_gallardo_crossgrad",
    "xghf36_salem_grav_tilt_zero",
    "xghf37_salem_mag_tilt_zero_deseam",
    "xghf38_magnetite_destr_potassic",
    "xghf39_redox_front_uth_grad",
    "xghf40_geotherm_diseq_800m",
    "xghf41_geotherm_diseq_2500m",
    "xghf42_probe2m_resid_plume",
    "xghf43_sinter_travertine_vent",
    "xghf44_usgs_convective_hf",
    "xghf45_transtension_saddle",
    "xghf46_mt_claycap_breach",
    "xghf47_tiger_lahontan_deconf",
    "xghf48_composite_crest_300m",
]

ALL_CHANNEL_NAMES = OFFICIAL_19_NAMES + STRUCTURAL_15_NAMES + XGHF_14_NAMES
N_CHANNELS = len(ALL_CHANNEL_NAMES)  # 48


def _robust_z_f16(arr: np.ndarray, foot: np.ndarray, clip: float = 8.0) -> np.ndarray:
    v = np.asarray(arr[foot], dtype=np.float64)
    v = np.where(np.isfinite(v), v, 0.0)
    med = float(np.median(v))
    q25, q75 = np.percentile(v, [25.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, float(np.std(v)), 1e-6)
    del v
    out = np.zeros(arr.shape, dtype=np.float16)
    sub = np.asarray(arr[foot], dtype=np.float32)
    sub = np.where(np.isfinite(sub), sub, np.float32(med))
    out[foot] = np.clip((sub - np.float32(med)) / np.float32(scale), -clip, clip).astype(np.float16)
    return out


def _read_official_band_filled(ds_tf: rasterio.DatasetReader, band_idx: int) -> np.ndarray:
    raw = ds_tf.read(band_idx)
    valid = np.isfinite(raw) & (raw > NODATA_SENTINEL_F32 * np.float32(0.5))
    out = raw.astype(np.float32, copy=True)
    del raw
    bad = ~valid
    if bad.any():
        _, idx = ndimage.distance_transform_edt(bad, return_distances=True, return_indices=True)
        out[bad] = out[idx[0][bad], idx[1][bad]]
        del idx
    return out


def _fill_nearest(raw: np.ndarray, valid: np.ndarray) -> np.ndarray:
    out = raw.astype(np.float32, copy=True)
    bad = ~valid
    if bad.any():
        _, idx = ndimage.distance_transform_edt(bad, return_distances=True, return_indices=True)
        out[bad] = out[idx[0][bad], idx[1][bad]]
        del idx
    return out


def _hessian_ridge(a: np.ndarray, sigma: float) -> np.ndarray:
    axx = ndimage.gaussian_filter(a, sigma, order=(0, 2), mode="nearest")
    ayy = ndimage.gaussian_filter(a, sigma, order=(2, 0), mode="nearest")
    axy = ndimage.gaussian_filter(a, sigma, order=(1, 1), mode="nearest")
    tmp = np.sqrt(np.maximum(((axx - ayy) * 0.5) ** 2 + axy * axy, 0.0))
    l1 = (axx + ayy) * 0.5 + tmp
    l2 = (axx + ayy) * 0.5 - tmp
    big = np.where(np.abs(l1) >= np.abs(l2), l1, l2)
    return np.maximum(-big, 0.0).astype(np.float32)


def _saddle_index(a: np.ndarray, sigma: float) -> np.ndarray:
    axx = ndimage.gaussian_filter(a, sigma, order=(0, 2), mode="nearest")
    ayy = ndimage.gaussian_filter(a, sigma, order=(2, 0), mode="nearest")
    axy = ndimage.gaussian_filter(a, sigma, order=(1, 1), mode="nearest")
    det = axx * ayy - axy * axy
    return np.sqrt(np.maximum(-det, 0.0)).astype(np.float32)


def _structure_tensor(a: np.ndarray, sigma: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gx = ndimage.gaussian_filter(a, sigma, order=(0, 1), mode="nearest")
    gy = ndimage.gaussian_filter(a, sigma, order=(1, 0), mode="nearest")
    jxx = ndimage.gaussian_filter(gx * gx, sigma, mode="nearest")
    jyy = ndimage.gaussian_filter(gy * gy, sigma, mode="nearest")
    jxy = ndimage.gaussian_filter(gx * gy, sigma, mode="nearest")
    tr = jxx + jyy + 1e-12
    coh = np.sqrt(np.maximum(((jxx - jyy) * 0.5) ** 2 + jxy * jxy, 0.0)) / tr
    two_phi = np.arctan2(2.0 * jxy, (jxx - jyy) + 1e-12)
    return coh.astype(np.float32), np.cos(two_phi).astype(np.float32), np.sin(two_phi).astype(np.float32)


def _utm_to_rowcol(utm_x: np.ndarray, utm_y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cols = np.floor((utm_x - 243350.0) / 100.0).astype(np.int32)
    rows = np.floor((4508550.0 - utm_y) / 100.0).astype(np.int32)
    return rows, cols


def _build_wellspring_geotherm_fields(ddir: Path, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray, int]:
    csv_path = ddir / "external" / "gdr_wellspring_in_footprint.csv"
    grid_imp = np.zeros(shape, dtype=np.float32)
    n_used = 0
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        allowed_cols = {"utm_x", "utm_y", "temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c"}
        assert "dist_known_fault_px" not in allowed_cols
        for row in reader:
            try:
                ux = float(row["utm_x"])
                uy = float(row["utm_y"])
            except (KeyError, ValueError):
                continue
            r = int((4508550.0 - uy) // 100.0)
            c = int((ux - 243350.0) // 100.0)
            if not (0 <= r < shape[0] and 0 <= c < shape[1]):
                continue
            vals_gt = []
            for k in ("geothermquartz_c", "geothermchalc_c", "geothermcat_c"):
                raw = row.get(k, "")
                if raw and raw != "nan":
                    try:
                        v = float(raw)
                        if 25.0 < v < 360.0:
                            vals_gt.append(v)
                    except ValueError:
                        pass
            t_surf = 14.0
            raw_t = row.get("temp_c", "")
            if raw_t and raw_t != "nan":
                try:
                    tv = float(raw_t)
                    if 0.0 < tv < 250.0:
                        t_surf = tv
                except ValueError:
                    pass
            t_res = max(vals_gt) if vals_gt else t_surf
            diseq = max(0.0, t_res - max(t_surf, 15.0))
            surf_anom = max(0.0, t_surf - 20.0)
            strength = float(np.log1p(0.65 * diseq + 1.15 * surf_anom))
            if strength > grid_imp[r, c]:
                grid_imp[r, c] = strength
            if strength > 0.0:
                n_used += 1
    f_800 = ndimage.gaussian_filter(grid_imp, sigma=8.0, mode="constant")
    f_2500 = ndimage.gaussian_filter(grid_imp, sigma=25.0, mode="constant")
    return f_800, f_2500, n_used


def _build_probe2m_field(ddir: Path, dem: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, int]:
    zpath = ddir / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    shp_rel = "2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo"
    with zipfile.ZipFile(zpath) as zf:
        shp_b = zf.read(shp_rel + ".shp")
        dbf_b = zf.read(shp_rel + ".dbf")

    n_rec = struct.unpack("<I", dbf_b[4:8])[0]
    hdr_len, rec_len = struct.unpack("<HH", dbf_b[8:12])
    fields = []
    pos = 32
    off = 1
    while pos < hdr_len - 1 and dbf_b[pos] != 0x0D:
        fname = dbf_b[pos : pos + 11].split(b"\x00")[0].decode("ascii", errors="ignore")
        flen = dbf_b[pos + 16]
        fields.append((fname, off, flen))
        off += flen
        pos += 32
    f_map = {nm: (o, l) for nm, o, l in fields}

    lons, lats, t2ms = [], [], []
    s_off = 100
    for i in range(n_rec):
        if s_off + 28 > len(shp_b):
            break
        rec_len_words = struct.unpack(">i", shp_b[s_off + 4 : s_off + 8])[0]
        content = shp_b[s_off + 8 : s_off + 8 + rec_len_words * 2]
        s_off += 8 + rec_len_words * 2
        if len(content) < 20:
            continue
        stype = struct.unpack("<i", content[:4])[0]
        if stype != 1:
            continue
        lon, lat = struct.unpack("<dd", content[4:20])
        rec_bytes = dbf_b[hdr_len + i * rec_len : hdr_len + (i + 1) * rec_len]
        o_t, l_t = f_map["T2m"]
        raw_t = rec_bytes[o_t : o_t + l_t].decode("ascii", errors="ignore").strip()
        try:
            t_val = float(raw_t)
        except ValueError:
            continue
        if 2.0 < t_val < 95.0 and -125.0 < lon < -110.0 and 35.0 < lat < 45.0:
            lons.append(lon)
            lats.append(lat)
            t2ms.append(t_val)

    transformer = pyproj.Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    ux, uy = transformer.transform(np.asarray(lons), np.asarray(lats))
    rows, cols = _utm_to_rowcol(ux, uy)
    t_arr = np.asarray(t2ms, dtype=np.float32)
    keep = (rows >= 0) & (rows < dem.shape[0]) & (cols >= 0) & (cols < dem.shape[1])
    rows, cols, t_arr = rows[keep], cols[keep], t_arr[keep]
    keep2 = foot[rows, cols]
    rows, cols, t_arr = rows[keep2], cols[keep2], t_arr[keep2]

    elev_pts = dem[rows, cols].astype(np.float64)
    X_reg = np.column_stack([np.ones_like(elev_pts), elev_pts, rows.astype(np.float64) / 1000.0])
    beta, *_ = np.linalg.lstsq(X_reg, t_arr.astype(np.float64), rcond=None)
    resid = np.maximum(0.0, t_arr.astype(np.float64) - X_reg @ beta)

    imp = np.zeros(dem.shape, dtype=np.float32)
    for r, c, rv in zip(rows, cols, resid):
        v = float(np.log1p(rv))
        if v > imp[r, c]:
            imp[r, c] = v
    plume = 0.65 * ndimage.gaussian_filter(imp, sigma=6.0, mode="constant") + 0.35 * ndimage.gaussian_filter(
        imp, sigma=18.0, mode="constant"
    )
    return plume, int(rows.size)


def _build_sinter_and_vent_field(ddir: Path, shape: tuple[int, int], foot: np.ndarray) -> tuple[np.ndarray, int]:
    imp = np.zeros(shape, dtype=np.float32)
    transformer = pyproj.Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    zpath = ddir / "external" / "paleo_geothermal_regional.zip"
    lons, lats, weights = [], [], []
    with zipfile.ZipFile(zpath) as zf:
        with zf.open("Paleo_geothermal_final.csv") as fh:
            reader = csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace"))
            for row in reader:
                try:
                    lon = float(row["Long_deg_NAD83"])
                    lat = float(row["Lat_deg_NAD83"])
                except (KeyError, ValueError):
                    continue
                dtype = (row.get("Deposit_type") or "").lower()
                w = 1.6 if ("sinter" in dtype or "silic" in dtype) else 1.15
                lons.append(lon)
                lats.append(lat)
                weights.append(w)
    n_in = 0
    if lons:
        ux, uy = transformer.transform(np.asarray(lons), np.asarray(lats))
        rs, cs = _utm_to_rowcol(ux, uy)
        for r, c, w in zip(rs, cs, weights):
            if 0 <= r < shape[0] and 0 <= c < shape[1] and foot[r, c]:
                imp[r, c] = max(imp[r, c], float(w))
                n_in += 1

    vpath = ddir / "external" / "gdr_volcanic_vents_in_footprint.csv"
    with vpath.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
            except (KeyError, ValueError):
                continue
            if 0 <= r < shape[0] and 0 <= c < shape[1] and foot[r, c]:
                imp[r, c] = max(imp[r, c], 1.0)
                n_in += 1

    plume = 0.6 * ndimage.gaussian_filter(imp, sigma=7.0, mode="constant") + 0.4 * ndimage.gaussian_filter(
        imp, sigma=20.0, mode="constant"
    )
    return plume, n_in


def _build_usgs_convective_heatflow_field(ddir: Path, shape: tuple[int, int], foot: np.ndarray) -> tuple[np.ndarray, int]:
    jpath = ddir / "external" / "sb_heat_flow_in_footprint.json"
    imp = np.zeros(shape, dtype=np.float32)
    n_in = 0
    if jpath.exists():
        data = json.loads(jpath.read_text())
        for rec in data.get("records", []):
            if "Point" not in rec.get("kinds", []):
                continue
            pts = rec.get("parts", [])
            if not pts or not pts[0]:
                continue
            ux, uy = pts[0][0]
            r = int((4508550.0 - uy) // 100.0)
            c = int((ux - 243350.0) // 100.0)
            if not (0 <= r < shape[0] and 0 <= c < shape[1]) or not foot[r, c]:
                continue
            hf_res = rec.get("hf_resid")
            hf_meas = rec.get("hf_meas")
            qc = str(rec.get("qc_code") or "")
            val = 0.0
            if isinstance(hf_res, (int, float)) and np.isfinite(hf_res) and hf_res > -500:
                val = max(0.0, float(hf_res))
            elif isinstance(hf_meas, (int, float)) and np.isfinite(hf_meas) and hf_meas > 85.0:
                val = float(hf_meas) - 85.0
            if qc == "G":
                val *= 1.35
            if val > 0.0:
                s = float(np.log1p(val))
                if s > imp[r, c]:
                    imp[r, c] = s
                n_in += 1
        del data
    plume = 0.55 * ndimage.gaussian_filter(imp, sigma=9.0, mode="constant") + 0.45 * ndimage.gaussian_filter(
        imp, sigma=28.0, mode="constant"
    )
    return plume, n_in


def build_or_load_xghf_stack(ddir: Path, wdir: Path, force_rebuild: bool = False) -> tuple[np.memmap, dict]:
    """Build or open the channel-first `(48, 3730, 3292)` `float16` memmap."""
    out_dat = wdir / "xghf_features_c48_f16.dat"
    out_meta = wdir / "xghf_features_c48_meta.json"
    mm_shape = (N_CHANNELS, EXPECTED_SHAPE[0], EXPECTED_SHAPE[1])
    if not force_rebuild and out_dat.exists() and out_meta.exists():
        meta = json.loads(out_meta.read_text())
        if meta.get("n_channels") == N_CHANNELS and meta.get("layout") == "CHW":
            mm = np.memmap(out_dat, mode="r", dtype=np.float16, shape=mm_shape)
            return mm, meta

    wdir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ddir / "sample_submission.tif") as ds_sub:
        foot = np.isfinite(ds_sub.read(1))

    mm = np.memmap(out_dat, mode="w+", dtype=np.float16, shape=mm_shape)

    # Step 1: Read official 19 bands one by one so peak RAM stays tiny
    with rasterio.open(ddir / "training_features.tif") as ds_tf:
        for b in range(1, 20):
            arr = _read_official_band_filled(ds_tf, b)
            mm[b - 1] = _robust_z_f16(arr, foot)
            mm.flush()
            del arr
            gc.collect()

        # Re-read only DEM (band 12) for DEM + probe2m + Lahontan steps
        dem = _read_official_band_filled(ds_tf, 12)

    # Step 2: [19..26] DEM structural derivatives
    mm[19] = _robust_z_f16(_hessian_ridge(dem, 1.0), foot)
    mm[20] = _robust_z_f16(_hessian_ridge(dem, 2.0), foot)
    mm[21] = _robust_z_f16(_hessian_ridge(dem, 3.5), foot)
    mm[22] = _robust_z_f16(dem - ndimage.grey_opening(dem, size=(5, 5)), foot)
    mm[23] = _robust_z_f16(ndimage.maximum_filter(dem, size=5) - ndimage.minimum_filter(dem, size=5), foot)
    st_coh, st_cos2, st_sin2 = _structure_tensor(dem, 2.0)
    mm[24] = np.where(foot, st_coh, 0.0).astype(np.float16)
    mm[25] = np.where(foot, st_cos2, 0.0).astype(np.float16)
    mm[26] = np.where(foot, st_sin2, 0.0).astype(np.float16)
    del st_coh, st_cos2, st_sin2
    mm.flush()
    gc.collect()

    # Step 3: [27..31] 1-m USGS 3DEP LiDAR scarp features
    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as ds_lid:
        lid_valid = (ds_lid.read(12) > 0).astype(np.float32)
        mm[27] = _robust_z_f16((ds_lid.read(1).astype(np.float32) / 255.0) * lid_valid, foot)
        mm[28] = _robust_z_f16((ds_lid.read(3).astype(np.float32) / 255.0) * lid_valid, foot)
        lid_asym = np.abs(ds_lid.read(6).astype(np.float32) - ds_lid.read(7).astype(np.float32)) / 255.0 * lid_valid
        mm[29] = _robust_z_f16(lid_asym, foot)
        del lid_asym
        mm[30] = _robust_z_f16((ds_lid.read(10).astype(np.float32) / 255.0) * lid_valid, foot)
        mm[31] = np.where(foot, lid_valid, 0.0).astype(np.float16)
        del lid_valid
    mm.flush()
    gc.collect()

    # Step 4: [32..33, 37..38] GeoDAWN radiometrics + upward-continued TMI + magnetite destruction
    with rasterio.open(ddir / "training_features.tif") as ds_tf:
        rtp = _read_official_band_filled(ds_tf, 2)
        tmi = _read_official_band_filled(ds_tf, 14)

    with rasterio.open(ddir / "external" / "geodawn_extensions_u8.tif") as ds_ext:
        ext_thk = ds_ext.read(1).astype(np.float32)
        ext_valid = (ext_thk > 0) & foot
        thk_filled = _fill_nearest(ext_thk, ext_valid)
        del ext_thk
        mm[32] = _robust_z_f16(thk_filled, foot)
        del thk_filled

        up150 = _fill_nearest(ds_ext.read(4).astype(np.float32), ext_valid)
        tmi_s = (tmi - float(np.median(tmi[foot]))) / (float(np.std(tmi[foot].astype(np.float64))) + 1e-6)
        up_s = (up150 - float(np.median(up150[foot]))) / (float(np.std(up150[foot].astype(np.float64))) + 1e-6)
        mm[33] = _robust_z_f16(np.abs(tmi_s - up_s), foot)
        del up150, tmi_s, up_s, tmi

        uk_filled = _fill_nearest(ds_ext.read(2).astype(np.float32), ext_valid)
        uth_filled = _fill_nearest(ds_ext.read(3).astype(np.float32), ext_valid)
        uy1, ux1 = np.gradient(ndimage.gaussian_filter(uth_filled, 1.5, mode="nearest"))
        uy2, ux2 = np.gradient(ndimage.gaussian_filter(uk_filled, 1.5, mode="nearest"))
        mm[38] = _robust_z_f16(np.hypot(ux1, uy1) + 0.7 * np.hypot(ux2, uy2), foot)
        del uk_filled, uth_filled, uy1, ux1, uy2, ux2, ext_valid
    mm.flush()
    gc.collect()

    with rasterio.open(ddir / "external" / "geodawn_rad_u8.tif") as ds_rad:
        rad_k = ds_rad.read(1).astype(np.float32)
        rad_th = ds_rad.read(2).astype(np.float32)
        rad_valid = (rad_k > 0) & (rad_th > 0) & foot
        k_th = _fill_nearest(rad_k, rad_valid) / (_fill_nearest(rad_th, rad_valid) + 1.0)
        del rad_k, rad_th, rad_valid
    rtp_trough = np.maximum(ndimage.gaussian_laplace(rtp, sigma=1.8, mode="nearest"), 0.0)
    k_th_z = np.clip(
        (k_th - float(np.median(k_th[foot]))) / (float(np.std(k_th[foot].astype(np.float64))) + 1e-6), -2.0, 5.0
    )
    mm[37] = _robust_z_f16(np.log1p(rtp_trough) * np.maximum(0.0, k_th_z + 0.5), foot)
    del rtp_trough, k_th, k_th_z
    mm.flush()
    gc.collect()

    # Step 5: [34..36] Gallardo-Meju Cross-Gradient & Salem Tilt-Zero Sharpness
    with rasterio.open(ddir / "training_features.tif") as ds_tf:
        grav = _read_official_band_filled(ds_tf, 13)
        grav_vg = _read_official_band_filled(ds_tf, 11)
        tmi_vg = _read_official_band_filled(ds_tf, 9)

    gy_g, gx_g = np.gradient(ndimage.gaussian_filter(grav, 1.2, mode="nearest"))
    gy_m, gx_m = np.gradient(ndimage.gaussian_filter(rtp, 1.2, mode="nearest"))
    del rtp
    ng = np.hypot(gx_g, gy_g)
    nm = np.hypot(gx_m, gy_m)
    prod = ng * nm
    cross_sin = np.abs(gx_g * gy_m - gy_g * gx_m) / (prod + 1e-6)
    del gx_g, gy_g, gx_m, gy_m
    med_prod = float(np.median(prod[foot])) + 1e-6
    mm[34] = _robust_z_f16(np.log1p(prod / med_prod) * (1.0 - np.clip(cross_sin, 0.0, 1.0)), foot)
    del prod, cross_sin

    grav_tilt = np.arctan2(grav_vg, ng + 1e-5)
    del grav_vg
    tgy, tgx = np.gradient(grav_tilt)
    mm[35] = _robust_z_f16(np.hypot(tgx, tgy) * np.exp(-(grav_tilt * grav_tilt) / 0.12), foot)
    del grav_tilt, tgy, tgx

    mag_tilt = np.arctan2(tmi_vg, nm + 1e-5)
    del tmi_vg, nm
    mag_tilt_deseam = ndimage.gaussian_filter(mag_tilt, sigma=(1.6, 0.9), mode="nearest")
    del mag_tilt
    mgy, mgx = np.gradient(mag_tilt_deseam)
    salem_mag = np.hypot(mgx, mgy) * np.exp(-(mag_tilt_deseam * mag_tilt_deseam) / 0.12)
    del mag_tilt_deseam, mgy, mgx
    blk_path = ddir / "external" / "acquisition_block_id_100m.tif"
    if blk_path.exists():
        with rasterio.open(blk_path) as ds_blk:
            blk = ds_blk.read(1)
        b_seam = (ndimage.maximum_filter(blk, size=5) != ndimage.minimum_filter(blk, size=5)) & foot
        seam_dist = ndimage.distance_transform_edt(~b_seam).astype(np.float32)
        salem_mag = salem_mag * np.clip(seam_dist / 4.0, 0.25, 1.0)
        del blk, b_seam, seam_dist
    mm[36] = _robust_z_f16(salem_mag, foot)
    del salem_mag
    mm.flush()
    gc.collect()

    # Step 6: [39..43] Real Geothermal / Hydrothermal Plume Layers
    gt_800, gt_2500, n_ws = _build_wellspring_geotherm_fields(ddir, EXPECTED_SHAPE)
    mm[39] = _robust_z_f16(gt_800, foot)
    mm[40] = _robust_z_f16(gt_2500, foot)
    del gt_800, gt_2500

    p2m_plume, n_p2m = _build_probe2m_field(ddir, dem, foot)
    mm[41] = _robust_z_f16(p2m_plume, foot)
    del p2m_plume

    sinter_plume, n_sinter = _build_sinter_and_vent_field(ddir, EXPECTED_SHAPE, foot)
    mm[42] = _robust_z_f16(sinter_plume, foot)
    del sinter_plume

    hf_plume, n_hf = _build_usgs_convective_heatflow_field(ddir, EXPECTED_SHAPE, foot)
    mm[43] = _robust_z_f16(hf_plume, foot)
    del hf_plume
    mm.flush()
    gc.collect()

    # Step 7: [44..47] Transtensional Relay Saddle, MT Breach, Road/Lahontan Deconfounder, 300m Crest
    with rasterio.open(ddir / "training_features.tif") as ds_tf:
        geod_2nd = _read_official_band_filled(ds_tf, 4)
        geod_dilat = _read_official_band_filled(ds_tf, 8)
        depth_base = _read_official_band_filled(ds_tf, 15)
        cond_surf = _read_official_band_filled(ds_tf, 17)

    dem_saddle = _saddle_index(dem, 2.5)
    grav_saddle = _saddle_index(grav, 3.0)
    del grav
    dilat_pos = np.maximum(
        0.0, (geod_dilat - float(np.median(geod_dilat[foot]))) / (float(np.std(geod_dilat[foot].astype(np.float64))) + 1e-6) + 0.5
    )
    strain_mag = np.maximum(
        0.0, (geod_2nd - float(np.median(geod_2nd[foot]))) / (float(np.std(geod_2nd[foot].astype(np.float64))) + 1e-6) + 0.5
    )
    del geod_dilat, geod_2nd
    mm[44] = _robust_z_f16(np.log1p(dem_saddle) * np.log1p(grav_saddle) * np.sqrt(dilat_pos * strain_mag + 0.05), foot)
    del dem_saddle, grav_saddle, dilat_pos, strain_mag

    cy, cx = np.gradient(ndimage.gaussian_filter(cond_surf, 2.0, mode="nearest"))
    by, bx = np.gradient(ndimage.gaussian_filter(depth_base, 2.0, mode="nearest"))
    del cond_surf, depth_base
    mm[45] = _robust_z_f16(np.sqrt(np.hypot(cx, cy) * np.hypot(bx, by) + 1e-8), foot)
    del cy, cx, by, bx

    with rasterio.open(ddir / "external" / "tiger_road_distance_m.tif") as ds_rd:
        rd_m = np.maximum(0.0, ds_rd.read(1).astype(np.float32))
    road_clean = np.clip(np.log1p(rd_m) / np.log1p(1000.0), 0.0, 1.5)
    del rd_m
    lahontan_band = np.exp(-((dem - 1336.0) / 14.0) ** 2) * np.exp(-ng / (float(np.median(ng[foot])) + 1e-6))
    del dem, ng
    mm[46] = _robust_z_f16(road_clean - 0.85 * lahontan_band, foot)
    del road_clean, lahontan_band
    mm.flush()
    gc.collect()

    raw_struct = (
        0.30 * mm[20].astype(np.float32)
        + 0.25 * mm[27].astype(np.float32)
        + 0.20 * mm[34].astype(np.float32)
        + 0.15 * mm[35].astype(np.float32)
        + 0.10 * mm[36].astype(np.float32)
    )
    crest_300m = raw_struct - ndimage.gaussian_filter(raw_struct, sigma=4.5, mode="nearest")
    mm[47] = _robust_z_f16(crest_300m, foot)
    del raw_struct, crest_300m
    mm.flush()
    gc.collect()

    meta = {
        "n_channels": N_CHANNELS,
        "layout": "CHW",
        "channel_names": ALL_CHANNEL_NAMES,
        "shape": list(mm_shape),
        "dtype": "float16",
        "footprint_pixels": int(foot.sum()),
        "real_point_observations_ingested": {
            "gdr_wellspring_geotherm_records": n_ws,
            "ingenious_2m_probe_records": n_p2m,
            "paleogeothermal_sinter_and_vents": n_sinter,
            "usgs_great_basin_heatflow_wells": n_hf,
        },
        "leakage_safeguards": {
            "reads_labels_tif": False,
            "reads_sgmc_tif": False,
            "drops_dist_known_fault_px": True,
        },
    }
    out_meta.write_text(json.dumps(meta, indent=2) + "\n")
    del mm
    gc.collect()
    mm_ro = np.memmap(out_dat, mode="r", dtype=np.float16, shape=mm_shape)
    return mm_ro, meta


def sample_pixels_chw(mm: np.memmap, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """Memory-clean `(N, C)` float32 extraction reading one contiguous channel slice at a time."""
    n = int(rows.size)
    c = mm.shape[0]
    out = np.empty((n, c), dtype=np.float32)
    for k in range(c):
        out[:, k] = mm[k][rows, cols].astype(np.float32)
    return out


def run_leakage_canary(
    mm: np.memmap,
    channel_names: list[str],
    foot: np.ndarray,
    labels: np.ndarray,
    max_allowed_auc: float = 0.90,
    seed: int = 20261027,
) -> dict:
    """Protocol Rule 4 Leakage Canary: test every single channel alone for AUC <= 0.90."""
    rng = np.random.default_rng(seed)
    d_lbl = ndimage.distance_transform_edt(~labels).astype(np.float32)
    pos_yx = np.nonzero(labels & foot)
    neg_yx = np.nonzero(foot & (d_lbl > 3.0))
    del d_lbl

    n_pos = min(25_000, pos_yx[0].size)
    n_neg = min(75_000, neg_yx[0].size)
    p_sel = rng.choice(pos_yx[0].size, size=n_pos, replace=False)
    n_sel = rng.choice(neg_yx[0].size, size=n_neg, replace=False)

    py, px = pos_yx[0][p_sel], pos_yx[1][p_sel]
    ny, nx = neg_yx[0][n_sel], neg_yx[1][n_sel]
    y = np.concatenate([np.ones(n_pos, dtype=np.int8), np.zeros(n_neg, dtype=np.int8)])

    per_channel = {}
    worst_name = ""
    worst_auc = 0.5
    for idx, cname in enumerate(channel_names):
        plane = mm[idx]
        vals = np.concatenate([plane[py, px].astype(np.float32), plane[ny, nx].astype(np.float32)])
        if float(vals.max() - vals.min()) < 1e-8:
            sym_auc = 0.5
            raw_auc = 0.5
        else:
            raw_auc = float(roc_auc_score(y, vals))
            sym_auc = max(raw_auc, 1.0 - raw_auc)
        per_channel[cname] = {
            "raw_auc": round(raw_auc, 5),
            "symmetric_auc": round(sym_auc, 5),
            "passed": sym_auc <= max_allowed_auc,
        }
        if sym_auc > worst_auc:
            worst_auc = sym_auc
            worst_name = cname

    return {
        "rule": f"single-feature symmetric AUC <= {max_allowed_auc:.2f} (Protocol Rule 4)",
        "n_channels_tested": len(channel_names),
        "n_pos_sampled": int(n_pos),
        "n_neg_sampled": int(n_neg),
        "max_symmetric_auc": round(worst_auc, 5),
        "max_channel": worst_name,
        "all_passed": worst_auc <= max_allowed_auc,
        "channels": per_channel,
    }
