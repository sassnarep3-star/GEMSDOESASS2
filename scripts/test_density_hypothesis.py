#!/usr/bin/env python3
"""Does the hidden-truth metric reward DENSER, spread-out predictions?

The official identity is

    DTI = T / (0.2 T + 0.2 F + 0.8 |G|)

With a *spread* prediction of n cells, T = |G| f(n) with f concave, and
F ~ n (1 - matched).  As n grows, f saturates at 1 while the 0.2 n term grows,
so DTI has an interior maximum.  Setting f = 1 - exp(-n c / M):

    DTI(n) = f / (0.2 f + 0.2 (n/|G|)(1-m) + 0.8)

With the nine-site inverse-variance fit (|G| ~ 39,000, T ~ 10,000 at n=37,654):

    n =  37,654   f=0.29  -> 0.24   (what the corpus actually submits)
    n = 150,000   f=0.60  -> 0.38
    n = 250,000   f=0.75  -> 0.40
    n = 450,000   f=0.93  -> 0.32

i.e. **the whole public corpus is ~4x under-dense**, which would explain why
every GEMSDOE site stalls in the 0.24-0.28 band while the public leaderboard
runs 0.34-0.45.  This script measures the curve instead of assuming it, on
both local targets, for three placement policies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402

SIZES = (20_000, 40_000, 80_000, 150_000, 250_000, 450_000, 800_000)


def main() -> int:
    oof = np.load(ROOT / ".cache" / "oof.npy")
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    coverage = np.isfinite(oof)
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    sgmc_off = sgmc & (d_qf > dti_eval.R_PX)
    targets = {"catalogue": qf, "sgmc_off": sgmc_off}

    rng = np.random.default_rng(2026)
    flat_cov = np.flatnonzero(coverage.ravel())
    p = np.where(coverage, oof, 0.0).ravel()
    # stratified weights: the model probability, flattened toward uniform so the
    # placement stays spread (pure top-k collapses into a few clusters)
    w_soft = (p + 0.02) ** 0.5
    w_soft = w_soft / w_soft.sum()
    w_cov = w_soft[flat_cov]
    w_cov = w_cov / w_cov.sum()

    rows = []
    for n in SIZES:
        rec = {"n": n}
        # A. uniform (space-filling) over the surveyed footprint
        pick = rng.choice(flat_cov, size=n, replace=False)
        m = np.zeros(coverage.size, bool); m[pick] = True
        for name, tgt in targets.items():
            rec[f"uniform_{name}"] = dti_eval.dti_terms(m.reshape(coverage.shape).astype(np.float32), tgt)
        # B. model-stratified spread (sampled with probability ~ sqrt(p))
        pick = rng.choice(flat_cov, size=n, replace=False, p=w_cov)
        m = np.zeros(coverage.size, bool); m[pick] = True
        for name, tgt in targets.items():
            rec[f"stratified_{name}"] = dti_eval.dti_terms(m.reshape(coverage.shape).astype(np.float32), tgt)
        # C. pure top-k of the model (the conventional choice)
        idx = np.argpartition(p, -n)[-n:]
        m = np.zeros(coverage.size, bool); m[idx] = True
        for name, tgt in targets.items():
            rec[f"topk_{name}"] = dti_eval.dti_terms(m.reshape(coverage.shape).astype(np.float32), tgt)
        rows.append(rec)
        print(f"n={n:>8,}  "
              + "  ".join(f"{pol}: cat={rec[pol + '_catalogue']['DTI']:.4f}/sgmc={rec[pol + '_sgmc_off']['DTI']:.4f}"
                          for pol in ("uniform", "stratified", "topk")), flush=True)

    best = {}
    for pol in ("uniform", "stratified", "topk"):
        for name in targets:
            key = f"{pol}_{name}"
            b = max(rows, key=lambda r: r[key]["DTI"])
            best[key] = {"n": b["n"], "DTI": b[key]["DTI"]}
    out = {"sizes": list(SIZES), "target_sizes": {k: int(v.sum()) for k, v in targets.items()},
           "rows": rows, "best": best,
           "evaluator_version": "EXACT-DTI-alpha0.2-beta0.8-R3px-v1"}
    (ROOT / "evidence" / "density_hypothesis.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(best, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
