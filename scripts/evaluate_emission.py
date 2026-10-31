#!/usr/bin/env python3
"""Choose the emission policy that maximises the exact official DTI.

Two *independent* targets are scored, because the competition truth is
"faults absent from the public catalogue" and there is no local copy of it:

``catalogue``
    The QFaults/INGENIOUS label raster, predicted out-of-fold with 20 km
    spatial blocks.  Measures raw fault-finding skill.

``sgmc_off``
    USGS State Geologic Map Compilation faults that sit more than 3 px
    (300 m) outside the catalogue.  This is a *different mapping programme*
    (state geologic maps, not the Quaternary fault database), so it is the
    closest local analogue of the hidden test set: faults somebody else
    mapped that the competition labels do not contain.

The second target is the one that matters for promotion.  A policy that only
wins on ``catalogue`` is winning on memorisation of the training labels.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof", default=".cache/oof.npy")
    ap.add_argument("--smooth", type=float, default=0.0)
    args = ap.parse_args()

    oof = np.load(ROOT / args.oof)
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    coverage = np.isfinite(oof)
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    sgmc_off = sgmc & (d_qf > dti_eval.R_PX)
    sgmc_on = sgmc & (d_qf <= dti_eval.R_PX)

    prob = oof.copy()
    if args.smooth > 0:
        prob = np.where(coverage, gaussian_filter(np.nan_to_num(prob), args.smooth), np.nan)

    print(f"coverage {coverage.sum():,}  catalogue {qf.sum():,}  "
          f"SGMC {sgmc.sum():,} (off-catalogue {sgmc_off.sum():,})", flush=True)

    # --- diagnostic: does the geophysical model see the SGMC faults? ------
    rng = np.random.default_rng(0)
    flat = np.flatnonzero(coverage.ravel())
    pick = rng.choice(flat, size=min(200_000, flat.size), replace=False)
    rand_vals = prob.ravel()[pick]
    diag = {
        "mean_prob_catalogue": float(np.nanmean(prob[qf])),
        "mean_prob_sgmc_offcatalogue": float(np.nanmean(prob[sgmc_off])),
        "mean_prob_random_covered": float(np.nanmean(rand_vals)),
        "p90_prob_random_covered": float(np.nanpercentile(rand_vals, 90)),
        "n_catalogue": int(qf.sum()),
        "n_sgmc_offcatalogue": int(sgmc_off.sum()),
        "n_sgmc_on_catalogue": int(sgmc_on.sum()),
    }
    print(json.dumps(diag, indent=1), flush=True)

    targets = {"catalogue": qf, "sgmc_off": sgmc_off}
    rows = dti_eval.sweep(prob, targets, allowed=coverage)
    for r in rows:
        print(f"q={r['q']:.3f} w={r['width']} n={r['n_cells']:>7,} "
              f"DTI_cat={r['catalogue']['DTI']:.4f} DTI_sgmc={r['sgmc_off']['DTI']:.4f} "
              f"T_cat={r['catalogue']['T']:.0f} F={r['catalogue']['F']:.0f}", flush=True)

    best_cat = max(rows, key=lambda r: r["catalogue"]["DTI"])
    best_sgmc = max(rows, key=lambda r: r["sgmc_off"]["DTI"])
    # promotion rule: rank by the *independent* target, break ties by the
    # catalogue score (a policy must not be catastrophic on either).
    ranked = sorted(rows, key=lambda r: (r["sgmc_off"]["DTI"], r["catalogue"]["DTI"]), reverse=True)
    out = {"diagnostic": diag, "sweep": rows, "best_catalogue": best_cat,
           "best_sgmc_off": best_sgmc, "ranked_by_sgmc_off": ranked[:5],
           "smooth_sigma": args.smooth,
           "evaluator_version": "EXACT-DTI-alpha0.2-beta0.8-R3px-v1"}
    (ROOT / "evidence" / "emission_sweep.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nBEST by catalogue:", json.dumps({k: best_cat[k] for k in ("q", "width", "n_cells")}))
    print("BEST by SGMC-off-catalogue:", json.dumps({k: best_sgmc[k] for k in ("q", "width", "n_cells")}),
          f"DTI={best_sgmc['sgmc_off']['DTI']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
