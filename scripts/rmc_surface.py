#!/usr/bin/env python3
"""RMC lane - Recall-Maximal Corridor propensity surface (catalogue-free by construction).

One file, three products, all written under `.cache/rmc/` (git-ignored):

  * `surface.npy`      float32 (3730, 3292) propensity in [0, 1]
  * `canary.json`      leakage canary: single-channel AUC on the holdout truth
  * `variants.json`    instrument table over emission geometries (evaluation later)

Every channel is derived from a *physical* field only.  No channel reads `labels.tif`,
`existing_faults.tif` or any scored submission raster, so the surface cannot inherit
catalogue geometry.  Channels (each rank-normalised to U[0,1] over the footprint):

  S1 pf_lineament   structure-tensor coherence x gradient magnitude on the tilt angle
                    (`tc`) with concurrence required from `tmi_hg` / `iso_grav_anom_hg`
  S2 scarp          1 m LiDAR scarp corridor (step + relief, coherence-weighted)
  S3 strain         geodetic dilatation / shear-rate / second-invariant corridor (sigma 5)
  S4 seismicity     inverse distance to nearest earthquake + intensity field
  S5 conduit        surface conductivity and its gradient (fluid pathway proxy)
  S6 basement       gradient of depth-to-basement-surface (basement step)
  A  geothermal     anchor proximity: GDR 2 m temperature probes, palaeo-geothermal
                    deposits, wellsprings (Gaussian, sigma 20 px = 2 km)

Propensity = rank of [ mean of the six rank-normalised structural channels ] x
(1 + 0.5 x rank of the geothermal anchor field).  The anchor term *modulates* structural
evidence and can never create a maximum on its own, because a spring or a hot probe in an
alluvial basin is not itself a fault.  Structural channels carry the fault evidence; the
anchor answers "which of these corridors actually moves fluid", the question the
fixed-budget dot lattices never ask.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.paths import data_dir  # noqa: E402

CACHE = ROOT / ".cache" / "rmc"
SIGMA_TENSOR = 3.0     # structure-tensor smoothing, px
SIGMA_STRAIN = 5.0     # geodesy is coarse (GPS ~1-2 km sampling)
SIGMA_SCARP = 1.5      # LiDAR attributes are already 100 m resampled
ANCHOR_SIGMA = 20.0    # 2 km - a vent field alters and fractures its host corridor broadly
ANCHOR_WEIGHT = 0.5
CHANNELS = ("S1_pf_lineament", "S2_scarp", "S3_strain", "S4_seismicity",
            "S5_conduit", "S6_basement", "A_geothermal")


def _band(band: int) -> np.ndarray:
    a = np.load(CACHE.parent / "features" / f"band-{band:02d}.npy")
    return a.astype(np.float32)


def rank_u01(a: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Rank-normalise footprint values to U[0,1]; zeros off-footprint. Robust to outliers."""
    out = np.zeros(a.shape, dtype=np.float32)
    v = a[foot].astype(np.float64)
    ok = np.isfinite(v)
    r = np.zeros(v.shape, dtype=np.float64)
    r[ok] = (np.argsort(np.argsort(v[ok])) + 0.5) / max(int(ok.sum()), 1)
    out[foot] = np.where(ok, r, 0.0).astype(np.float32)
    return out


def coherence(field: np.ndarray, foot: np.ndarray, sigma: float = SIGMA_TENSOR) -> np.ndarray:
    """Hale-style structure tensor lineament coherence in [0,1] (1 = perfectly linear edge)."""
    f = np.where(foot, np.nan_to_num(field, nan=0.0, posinf=0.0, neginf=0.0), 0.0)
    f = ndi.gaussian_filter(f.astype(np.float32), sigma)
    gy, gx = np.gradient(f)
    jxx = ndi.gaussian_filter(gx * gx, sigma)
    jyy = ndi.gaussian_filter(gy * gy, sigma)
    jxy = ndi.gaussian_filter(gx * gy, sigma)
    tr = jxx + jyy
    det = jxx * jyy - jxy * jxy
    disc = np.sqrt(np.maximum(tr * tr - 4.0 * det, 0.0))
    lam1 = 0.5 * (tr + disc)
    lam2 = 0.5 * (tr - disc)
    coh = lam1 - lam2
    energy = np.sqrt(np.maximum(lam1, 0.0))
    with np.errstate(invalid="ignore", divide="ignore"):
        c = np.where(energy > 0, coh / np.maximum(tr, 1e-12), 0.0)
    return np.where(foot, np.clip(c, 0.0, 1.0), 0.0).astype(np.float32), energy.astype(np.float32)


def build(foot: np.ndarray, ext: pathlib.Path) -> dict[str, np.ndarray]:
    ch: dict[str, np.ndarray] = {}

    # S1 potential-field lineament coherence with multi-field concurrence ----------
    tc = _band(6)          # tilt angle / total curvature (edge-normalised)
    coh, energy = coherence(tc, foot)
    hg_mag = np.hypot(*np.gradient(ndi.gaussian_filter(np.nan_to_num(_band(3), nan=0.0), 1.0)))
    gv_mag = np.hypot(*np.gradient(ndi.gaussian_filter(np.nan_to_num(_band(18), nan=0.0), 1.0)))
    conc = rank_u01(np.minimum(hg_mag, gv_mag), foot) * rank_u01(hg_mag + gv_mag, foot)
    ch["S1_pf_lineament"] = rank_u01(coh * rank_u01(energy, foot), foot) * (0.5 + 0.5 * conc)

    # S2 1 m LiDAR scarp corridor -------------------------------------------------
    with rasterio.open(ext / "lidar_scarp_features_u8.tif") as ds:
        names = {n: i for i, n in enumerate(ds.descriptions)}
        step = ds.read(names["step_max"] + 1).astype(np.float32)
        relief = ds.read(names["relief"] + 1).astype(np.float32)
        coh100 = ds.read(names["coh100"] + 1).astype(np.float32)
        valid = ds.read(names["valid"] + 1) > 0
    sc = np.where(valid & foot, step * 0.5 + relief * 0.5, 0.0)
    sc = ndi.gaussian_filter(sc.astype(np.float32), SIGMA_SCARP)
    c100 = np.where(valid & foot, coh100 / 255.0, 0.0).astype(np.float32)
    ch["S2_scarp"] = rank_u01(sc, foot) * (0.4 + 0.6 * c100)

    # S3 geodetic strain corridor --------------------------------------------------
    dil = ndi.gaussian_filter(np.nan_to_num(_band(8), nan=0.0), SIGMA_STRAIN)
    shr = ndi.gaussian_filter(np.nan_to_num(_band(7), nan=0.0), SIGMA_STRAIN)
    inv = ndi.gaussian_filter(np.nan_to_num(_band(4), nan=0.0), SIGMA_STRAIN)
    ch["S3_strain"] = rank_u01(np.abs(dil), foot) * 0.4 + rank_u01(np.abs(shr), foot) * 0.35 \
        + rank_u01(inv, foot) * 0.25

    # S4 seismicity ----------------------------------------------------------------
    deq = np.nan_to_num(_band(10), nan=1e6)      # distance to nearest earthquake, m
    ieq = np.nan_to_num(_band(16), nan=0.0)       # earthquake intensity / density
    ch["S4_seismicity"] = 0.6 * (1.0 - rank_u01(deq, foot)) + 0.4 * rank_u01(ieq, foot)

    # S5 conductivity conduit ------------------------------------------------------
    cond = np.nan_to_num(_band(17), nan=0.0)
    cg = np.hypot(*np.gradient(ndi.gaussian_filter(cond, 2.0)))
    ch["S5_conduit"] = 0.5 * rank_u01(cond, foot) + 0.5 * rank_u01(cg, foot)

    # S6 basement step --------------------------------------------------------------
    dep = np.nan_to_num(_band(15), nan=0.0)
    dg = np.hypot(*np.gradient(ndi.gaussian_filter(dep, 3.0)))
    ch["S6_basement"] = rank_u01(dg, foot)

    # A geothermal anchor field -----------------------------------------------------
    anchor = np.zeros(foot.shape, dtype=np.float32)
    for f in ("derived_gdr_2m_probes_100m_u8.tif", "derived_gdr_paleo_100m_u8.tif"):
        p = ext / f
        if not p.is_file():
            p2 = pathlib.Path("/home/user/registry/GEMSDOE30/data/external") / f
            p = p2 if p2.is_file() else p
        if not p.is_file():
            raise FileNotFoundError(f"missing anchor raster {f}")
        with rasterio.open(p) as ds:
            a = ds.read(1)
        pts = (a == 1) & foot
        anchor = np.maximum(anchor, np.exp(-(ndi.distance_transform_edt(~pts) ** 2)
                                           / (2.0 * ANCHOR_SIGMA ** 2)).astype(np.float32))
    # wellsprings: UTM 11N point list from the GDR CSV (official, free)
    import csv
    wp = ext / "gdr_wellspring_in_footprint.csv"
    if wp.is_file():
        xs, ys = [], []
        with wp.open(newline="", encoding="utf-8", errors="replace") as fh:
            rd = csv.DictReader(fh)
            cols = {c.lower().strip(): c for c in (rd.fieldnames or [])}
            cx = next((cols[k] for k in cols if k.startswith("x")), None)
            cy = next((cols[k] for k in cols if k.startswith("y")), None)
            for row in rd:
                try:
                    xs.append(float(row[cx])); ys.append(float(row[cy]))
                except (TypeError, ValueError, KeyError):
                    continue
        if xs:
            # UTM -> grid index using the reference transform (100 m, x0 243350, y0 4508550)
            gx = np.asarray(xs, float)
            gy = np.asarray(ys, float)
            c0 = ((gx - 243350.0) / 100.0).astype(int)
            r0 = ((4508550.0 - gy) / 100.0).astype(int)
            keep = (c0 >= 0) & (c0 < foot.shape[1]) & (r0 >= 0) & (r0 < foot.shape[0])
            if keep.any():
                seed = np.zeros(foot.shape, dtype=bool)
                seed[r0[keep], c0[keep]] = True
                seed &= foot
                if seed.any():
                    anchor = np.maximum(anchor, np.exp(-(ndi.distance_transform_edt(~seed) ** 2)
                                                       / (2.0 * ANCHOR_SIGMA ** 2)).astype(np.float32))
    ch["A_geothermal"] = anchor
    return ch


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="rebuild the cached surface")
    args = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    ddir = data_dir()
    ext = pathlib.Path("/home/user/registry/GEMSDOE24/data/external")
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))

    surf_p = CACHE / "surface.npy"
    ch_p = CACHE / "channels.npz"
    if args.force or not surf_p.exists():
        ch = build(foot, ext)
        structural = [ch[n] for n in CHANNELS if n != "A_geothermal"]
        base = (sum(structural) / len(structural)).astype(np.float32)
        # Anchors *modulate* structural evidence; they never create a new maximum on
        # their own (a spring in an alluvial basin is not a fault).
        boost = base * (1.0 + ANCHOR_WEIGHT * rank_u01(ch["A_geothermal"], foot))
        surf = np.where(foot, rank_u01(boost, foot), 0.0).astype(np.float32)
        np.save(surf_p, surf)
        np.savez_compressed(ch_p, **{k: v.astype(np.float32) for k, v in ch.items()},
                            foot=foot)
        print(f"[rmc] built surface, mass={float(surf[foot].sum()):.1f}, "
              f"nonzero footprint px={int((surf > 0).sum())}")
    else:
        surf = np.load(surf_p)
        print(f"[rmc] reusing cached surface {surf_p}")
    receipt = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_class": "METHOD-ARTIFACT (catalogue-free propensity surface)",
        "grid": {"shape": list(surf.shape), "crs": "EPSG:32611", "resolution_m": 100},
        "channels": list(CHANNELS),
        "anchor_sigma_px": ANCHOR_SIGMA, "anchor_weight": ANCHOR_WEIGHT,
        "catalogue_inputs_used": 0,
        "surface_sha256": __import__("hashlib").sha256(surf_p.read_bytes()).hexdigest(),
        "footprint_px": int(foot.sum()), "surface_px_gt0": int((surf > 0).sum()),
    }
    (CACHE / "surface_receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps(receipt, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
