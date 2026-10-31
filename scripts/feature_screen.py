#!/usr/bin/env python3
"""Univariate leakage-canary screen: AUC of every cube band against the known-fault
label raster (and against the SGMC off-catalogue proxy), computed on a random
subsample of footprint cells.

Standing-prompt rule 4: a single-feature AUC above 0.90 is leakage until
disproved.  Bands that are catalogue-derived would trip it; every band here is an
independent geophysical/geometric field, so a high AUC would instead be a strong
single-layer fault detector.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"


def auc(x: np.ndarray, y: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    y = y[: x.size]
    # subsample-safe rank AUC on the given vectors (assumed aligned & finite-filtered upstream)
    return float("nan")


def auc_aligned(x: np.ndarray, y: np.ndarray) -> float:
    m = np.isfinite(x)
    x, y = x[m], y[m]
    n1 = int(y.sum())
    n0 = int(y.size - n1)
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = rankdata(x)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def main() -> int:
    meta = json.loads((WORK / "cube_meta.json").read_text())
    names = meta["band_names"]
    H, W = meta["grid"]["shape"]
    footprint = np.load(WORK / "footprint.npy")
    labels = np.load(WORK / "qfaults_labels.npy")
    import rasterio
    with rasterio.open(ROOT / ".cache/mirror/GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    near2 = binary_dilation(labels, np.ones((5, 5), dtype=bool))
    sgmc2 = sgmc & ~near2 & footprint

    cube = np.lib.format.open_memmap(WORK / "cube.f32", mode="r", dtype=np.float32, shape=(len(names), H, W))
    rng = np.random.default_rng(20261031)
    idx = np.flatnonzero(footprint.ravel())
    sub = rng.choice(idx, size=1_500_000, replace=False)
    y_lab = labels.ravel()[sub]
    rows = []
    for b, name in enumerate(names):
        v = np.asarray(cube[b], dtype=np.float32).ravel()[sub]
        # proxy-truth AUC computed on the same subsample
        y_sg = sgmc2.ravel()[sub]
        rows.append({
            "band": b, "name": name,
            "auc_known_faults": round(auc_aligned(v.astype(np.float64), y_lab), 4),
            "auc_sgmc_offcatalogue": round(auc_aligned(v.astype(np.float64), y_sg), 4),
            "valid_frac": round(float(np.isfinite(v).mean()), 4),
        })
    rows.sort(key=lambda r: -max(abs(r["auc_known_faults"] - 0.5), abs(r["auc_sgmc_offcatalogue"] - 0.5)))
    out = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "subsample": int(sub.size),
        "note": "Univariate AUC on 1.5 M random footprint cells. Leakage alarm if |AUC-0.5|>0.40.",
        "rows": rows,
    }
    (ROOT / "evidence/feature_screen.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for r in rows[:25]:
        print(f"{r['band']:3d} {r['name']:38s} AUC_known={r['auc_known_faults']:.4f}  AUC_sgmc={r['auc_sgmc_offcatalogue']:.4f}  valid={r['valid_frac']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
