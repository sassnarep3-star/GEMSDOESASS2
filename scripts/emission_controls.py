"""Does the geophysical score buy anything on a fault map it never saw?

The promoted file tilts an emission density by a LightGBM score and reweights it
with a soft collar at 1.2 km outside the mapped catalogue.  Both moves were
chosen on the catalogue, which is also the model's training label.  The only
target in this repository that is independent of both is the SGMC compilation
(83,593 cells, different mapping programme, different convention).

So: same budget, same seed, four densities.
    uniform   tilt 0.00, collar 0     -- no geology at all, pure space filling
    model     tilt 0.35, collar 0     -- geophysics, no collar
    collar    tilt 0.35, collar 0.85  -- the promoted file
    sharp     tilt 1.00, collar 0     -- density proportional to the model
If `uniform` wins on the independent target, the geophysical model has no
transferable skill and the honest submission is a space-filling design.
If `collar` wins, the promotion stands on evidence outside its training label.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.design import jittered_design  # noqa: E402

ARMS = [
    ("uniform", 0.00, 0.00),
    ("model", 0.35, 0.00),
    ("collar", 0.35, 0.85),
    ("sharp", 1.00, 0.00),
]


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

    out = {"scope": "MODEL ESTIMATE, never an organiser score",
           "targets": {k: int(v.sum()) for k, v in targets.items()}, "arms": []}
    for n in (250_000, 400_000):
        for name, tilt, collar in ARMS:
            w = smooth if collar == 0 else smooth * ((1.0 - collar) + collar * near)
            mask = jittered_design(w, domain, n, tilt=tilt, seed=20261031)
            rec = {"arm": name, "n_requested": n, "n_cells": int(mask.sum()),
                   "tilt": tilt, "collar": collar}
            for tname, tgt in targets.items():
                t = dti_eval.dti_terms(mask.astype(np.float32), tgt)
                rec[tname] = dict(DTI=round(t["DTI"], 4), T=round(t["T"], 1),
                                  F=round(t["F"], 1), G=int(t["G"]),
                                  coverage_r=round(t["T"] / t["G"], 4))
            out["arms"].append(rec)
            print(f"n={n:>7,} {name:<8} cells={rec['n_cells']:>7,}  "
                  + "  ".join(f"{k}: DTI={rec[k]['DTI']:.4f} r={rec[k]['coverage_r']:.3f}"
                              for k in targets), flush=True)
            del mask

    # rank each arm on each target, 1 = best
    for tname in targets:
        order = sorted(out["arms"], key=lambda r: -r[tname]["DTI"])
        for i, r in enumerate(order):
            r[f"rank_{tname}"] = i + 1
    out["verdict"] = {
        "best_on_independent": max(out["arms"], key=lambda r: r["sgmc_off"]["DTI"])["arm"],
        "best_on_catalogue": max(out["arms"], key=lambda r: r["catalogue"]["DTI"])["arm"],
        "note": ("The independent target is the only one that can distinguish transferable "
                 "skill from fitting the training label. A tie or a uniform win means the "
                 "geophysical tilt is not justified by evidence outside the catalogue."),
    }
    (ROOT / "evidence" / "emission_controls.json").write_text(json.dumps(out, indent=1) + "\n")
    print("verdict:", json.dumps(out["verdict"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
