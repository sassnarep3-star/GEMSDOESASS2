"""Final submission: emission density proportional to ONE physical band.

What the four experiments in this lane established (evidence/):
  emission_optimum.json    the nine-site density law fits to +-0.005; the budget
                           optimum is near 3e5 cells; dilated "ribbons" lose.
  emission_controls.json   a fitted 125-feature model *loses* 7-33 % on a fault
                           compilation it never saw, and the more it is trusted
                           (tilt 0 -> 1) the worse the transfer.  Overfit.
  sgmc_transfer_auc.json   one raw band does transfer: band 19
                           (detrended-elevation slope) separates faults from
                           background at AUC 0.757 on that same independent
                           compilation -- higher than the model.
  b19_confound_check.json  part of that is terrain context (within deciles of
                           detrended elevation the AUC falls to 0.64), which is
                           stated rather than hidden.
  feature_tilt_sweep.json  density proportional to smoothed band 19 at 3e5
                           cells scores 0.403 on the independent target versus
                           0.295 for a space-filling lattice of the same size.

So the submission is: 300,000 cells, density proportional to a 500 m-smoothed
detrended-elevation-slope field, with every cell inside 100 m of the public fault
database removed.  One band, one smoothing scale, one budget -- three choices,
none of them fitted to the catalogue.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.design import jittered_design  # noqa: E402
from gems_sass2.submission import sha256_file, write_submission_pair  # noqa: E402

STEM = "gemsass2-slopetilt-300k-20261031"
NAME = "GEMSASS2-SLOPETILT-300K-20261031"
NOTE = ("density - detrended-elevation-slope prior at the metric optimum; "
        "zero cells on the public fault database")
N = 300_000
TILT = 1.0
SIGMA = 5.0
SEED = 20261031


def main() -> int:
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    with rasterio.open(ROOT / ".cache" / "features" / "training_features.tif") as ds:
        b19 = ds.read(19)
        cov = b19 != ds.nodata
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    tgt = {"catalogue": qf, "sgmc_off": sgmc & (d_qf > dti_eval.R_PX)}
    del labels, sgmc

    w = np.where(cov, np.nan_to_num(b19, nan=0.0), 0.0).astype(np.float32)
    w = gaussian_filter(w, SIGMA).astype(np.float32)
    dom = foot & cov & ~binary_dilation(qf, np.ones((3, 3), bool))
    del b19

    t0 = time.time()
    mask = jittered_design(w, dom, N, tilt=TILT, seed=SEED)
    print(f"design {mask.sum():,} cells in {time.time() - t0:.0f}s", flush=True)
    terms = {k: dti_eval.dti_terms(mask.astype(np.float32), t) for k, t in tgt.items()}
    for k, v in terms.items():
        print(f"  {k:9s} DTI={v['DTI']:.4f} T={v['T']:,.0f} F={v['F']:,.0f} G={v['G']:,}")

    info = write_submission_pair(mask.astype(np.float32), ROOT / "docs" / "downloads", STEM,
                                 ROOT / "data" / "bridge" / "sample_submission.tif",
                                 ROOT / "data" / "bridge" / "labels.tif")
    primary = ROOT / "docs" / "downloads" / f"{STEM}-zeros.tif"
    out = {
        "scope": "MODEL ESTIMATE, never an organiser score",
        "design": {"n_requested": N, "tilt": TILT, "seed": SEED,
                   "weight": "band 19 (detrended elevation slope), gaussian sigma 5 px = 500 m",
                   "domain": "official footprint & feature coverage & not within 1 px of the catalogue",
                   "rationale": "highest transfer AUC of the 19 official bands on an independent fault compilation"},
        "local_DTI": terms,
        "submission": {
            "stem": STEM, "name": NAME, "note": NOTE, "note_chars": len(NOTE),
            "n_cells": int(mask.sum()), "sha256": sha256_file(primary),
            "validation": info["zeros"], "files": {"zeros": str(primary),
                                                   "nan": str(ROOT / "docs" / "downloads" / f"{STEM}-nan.tif"),
                                                   "zip": info["zip"]["path"]},
        },
    }
    (ROOT / "evidence" / "final_slopetilt_submission.json").write_text(json.dumps(out, indent=1) + "\n")
    print("sha256:", out["submission"]["sha256"])
    print("valid:", info["zeros"]["all_passed"], "| note chars:", len(NOTE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
