"""Final emission selector: space filling, minus the cells the organisers already know.

Three experiments in this lane (see evidence/):
  1. emission_optimum.json  -- the nine-site density law fits to +-0.005 and the
     budget sweep peaks near 3.5e5 cells; ribbons (dilated dots) are much worse.
  2. emission_controls.json -- a geophysical tilt that looks strong on the
     catalogue *loses* 7-33 % on the independent SGMC compilation; the more tilt,
     the worse the transfer.  That is overfitting to the training label.
  3. emission_avoidance.json -- at equal budget the only structure that helps an
     independent fault map is removing predictions from cells the public database
     already calls a fault (+2.8 %, both seeds).

So the selected design is deliberately dumb: a space-filling lattice at the
density optimum, with predictions deleted wherever the catalogue already has a
fault.  It carries no fitted geology, and therefore cannot overfit one.

This script repeats the grid one step finer, picks by the independent target,
writes the submission through the shared writer, and emits the run card.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.design import jittered_design  # noqa: E402
from gems_sass2.submission import sha256_file, write_submission_pair  # noqa: E402

NS = (250_000, 300_000, 350_000, 400_000)
RADII = (0, 1, 2, 3)
SEED = 20261031
STEM = "gemsass2-catfree-300k-20261031"
NAME = "GEMSASS2-CATFREE-300K-20261031"
NOTE = "space-filling at the metric's density optimum; zero cells on the public fault database"


def gate(mask: np.ndarray, sf: np.ndarray, n_pos: int) -> float:
    """0-1 scaled rank correlation is not needed here: the design is a lattice."""
    return float(mask.sum()) / max(n_pos, 1)


def main() -> int:
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    with rasterio.open(ROOT / ".cache" / "features" / "training_features.tif") as ds:
        covered = np.any(ds.read(1) != np.float32(-3.4028235e38), axis=0)
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    tgt = {"catalogue": qf, "sgmc_off": sgmc & (d_qf > dti_eval.R_PX)}
    base_domain = footprint & covered
    del labels, sgmc, footprint

    ones = np.ones((int(base_domain.shape[0]), int(base_domain.shape[1])), np.float32)
    out = {"scope": "MODEL ESTIMATE, never an organiser score", "seed": SEED,
           "grid": [], "rule": "maximise DTI on sgmc_off (never in training); catalogue reported only"}
    t0 = time.time()
    previous = None
    if "--skip-grid" in sys.argv:
        previous = json.loads((ROOT / "evidence" / "final_avoidance_submission.json").read_text())
        out["grid"] = previous["grid"]
        RADII = (previous["selected"]["avoid_radius_px"],)
        NS = (previous["selected"]["n_requested"],)
    for radius in RADII:
        dom = base_domain
        if radius:
            dom = base_domain & ~binary_dilation(qf, np.ones((2 * radius + 1,) * 2, bool))
        for n in NS:
            mask = jittered_design(ones, dom, n, tilt=0.0, seed=SEED)
            rec = {"avoid_radius_px": radius, "n_requested": n, "n_cells": int(mask.sum())}
            for k, t in tgt.items():
                tt = dti_eval.dti_terms(mask.astype(np.float32), t)
                rec[k] = dict(DTI=round(tt["DTI"], 4), T=round(tt["T"], 1),
                              F=round(tt["F"], 1), coverage_r=round(tt["T"] / tt["G"], 4))
            out["grid"].append(rec)
            print(f"r={radius} n={n:>7,} cells={rec['n_cells']:>7,} "
                  f"sgmc={rec['sgmc_off']['DTI']:.4f} cat={rec['catalogue']['DTI']:.4f} "
                  f"({time.time() - t0:.0f}s)", flush=True)
            del mask
    best = (previous["selected"] if previous
            else max(out["grid"], key=lambda r: r["sgmc_off"]["DTI"]))
    out["selected"] = best
    print("selected:", json.dumps(best))

    # confirm on a second seed before committing
    radius, n = best["avoid_radius_px"], best["n_requested"]
    dom = base_domain
    if radius:
        dom = base_domain & ~binary_dilation(qf, np.ones((2 * radius + 1,) * 2, bool))
    cfg = []
    for seed in (SEED, 20261101):
        m = jittered_design(ones, dom, n, tilt=0.0, seed=seed)
        tt = dti_eval.dti_terms(m.astype(np.float32), tgt["sgmc_off"])
        cfg.append(dict(seed=seed, n_cells=int(m.sum()), sgmc_DTI=round(tt["DTI"], 4)))
        print(f"confirm seed={seed} cells={cfg[-1]['n_cells']:,} sgmc={cfg[-1]['sgmc_DTI']:.4f}",
              flush=True)
        if seed == SEED:
            final = m.astype(np.float32)
    out["seed_confirmation"] = cfg
    out["seed_spread_sgmc"] = round(max(c["sgmc_DTI"] for c in cfg) - min(c["sgmc_DTI"] for c in cfg), 4)

    # ---- write through the shared writer (it also zeroes every catalogue cell)
    info = write_submission_pair(final, ROOT / "docs" / "downloads", STEM,
                                 ROOT / "data" / "bridge" / "sample_submission.tif",
                                 ROOT / "data" / "bridge" / "labels.tif")
    primary = ROOT / "docs" / "downloads" / f"{STEM}-zeros.tif"
    sha = sha256_file(primary)
    out["submission"] = dict(stem=STEM, name=NAME, note=NOTE, note_chars=len(NOTE),
                             sha256=sha, n_cells=int(final.sum()),
                             validation=info["zeros"],
                             files={"zeros": str(primary), "zip": info["zip"]["path"],
                                    "nan": str(ROOT / "docs" / "downloads" / f"{STEM}-nan.tif")})
    (ROOT / "evidence" / "final_avoidance_submission.json").write_text(json.dumps(out, indent=1) + "\n")
    print("sha256:", sha)
    print("valid:", info["zeros"]["all_passed"])
    print("cells:", int(final.sum()), "note chars:", len(NOTE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
