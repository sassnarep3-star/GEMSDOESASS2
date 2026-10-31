"""Space filling plus catalogue avoidance: the only structure with a prior reason.

The competition states the target faults are *absent from the public database*.
So a prediction that lands on the catalogue is, by the organisers' own definition,
at best redundant and at worst a guaranteed false positive.  That is a reason to
avoid the catalogue that does not depend on any model, and therefore cannot
overfit the training label.

Arms, all at one budget and two seeds:
    uniform      tilt 0.00, no avoidance            -- the incumbent control
    softcollar   tilt 0.00, collar 0.85 (1.2 km)    -- space filling, 1.2 km ring
    hardavoid    tilt 0.00, weight 0 within 1 px    -- no prediction on a known fault
    promoted     tilt 0.35, collar 0.85             -- the file currently on the site

The independent target (SGMC, never in training) decides.  The catalogue target is
reported as a diagnostic only, because every model-tilted arm was selected on it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.design import jittered_design  # noqa: E402

BUDGET = 350_000
SEEDS = (20261031, 7)


def main() -> int:
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    targets = {"catalogue": qf, "sgmc_off": sgmc & (d_qf > dti_eval.R_PX)}
    del labels, sgmc

    prob = np.load(ROOT / ".cache" / "prob_final.npy")
    covered = np.isfinite(prob)
    flat = np.where(covered, np.nan_to_num(prob), 0.0)
    smooth = np.where(covered, gaussian_filter(flat, 2.0), 0.0).astype(np.float32)
    del prob, flat
    near = np.exp(-0.5 * ((d_qf - 12.0) / 14.0) ** 2).astype(np.float32)
    domain = footprint & covered
    hard = binary_dilation(qf, np.ones((3, 3), bool))
    ones = np.ones_like(smooth)

    out = {"scope": "MODEL ESTIMATE, never an organiser score", "budget": BUDGET,
           "seeds": list(SEEDS), "arms": []}
    for seed in SEEDS:
        for name, tilt in (("uniform", 0.0), ("softcollar", 0.0),
                           ("hardavoid", 0.0), ("promoted", 0.35)):
            if name == "uniform":
                w, dom = ones, domain
            elif name == "softcollar":
                w, dom = (0.15 + 0.85 * near), domain
            elif name == "hardavoid":
                w, dom = ones, (domain & ~hard)
            else:
                w, dom = smooth * (0.15 + 0.85 * near), domain
            mask = jittered_design(w, dom, BUDGET, tilt=tilt, seed=seed)
            rec = {"arm": name, "seed": seed, "tilt": tilt,
                   "n_cells": int(mask.sum()),
                   "on_catalogue_cells": int((mask & qf).sum())}
            for tname, tgt in targets.items():
                t = dti_eval.dti_terms(mask.astype(np.float32), tgt)
                rec[tname] = dict(DTI=round(t["DTI"], 4), T=round(t["T"], 1),
                                  F=round(t["F"], 1), coverage_r=round(t["T"] / t["G"], 4))
            out["arms"].append(rec)
            print(f"seed={seed:<9} {name:<11} cells={rec['n_cells']:>7,} "
                  f"oncat={rec['on_catalogue_cells']:>5,}  "
                  + "  ".join(f"{k}: {rec[k]['DTI']:.4f}" for k in targets), flush=True)
            del mask

    summary = {}
    for name in ("uniform", "softcollar", "hardavoid", "promoted"):
        rows = [r for r in out["arms"] if r["arm"] == name]
        summary[name] = {
            "sgmc_mean": round(float(np.mean([r["sgmc_off"]["DTI"] for r in rows])), 4),
            "sgmc_min": round(float(np.min([r["sgmc_off"]["DTI"] for r in rows])), 4),
            "cat_mean": round(float(np.mean([r["catalogue"]["DTI"] for r in rows])), 4),
        }
    out["summary"] = summary
    best = max(summary, key=lambda k: summary[k]["sgmc_min"])
    out["verdict"] = {
        "best_on_independent_worst_seed": best,
        "rule": ("rank by the WORST seed on the independent target, so a single lucky "
                 "draw cannot promote an arm"),
    }
    (ROOT / "evidence" / "emission_avoidance.json").write_text(json.dumps(out, indent=1) + "\n")
    for k, v in summary.items():
        print(f"{k:<11} sgmc mean {v['sgmc_mean']:.4f} min {v['sgmc_min']:.4f} | cat {v['cat_mean']:.4f}")
    print("verdict:", json.dumps(out["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
