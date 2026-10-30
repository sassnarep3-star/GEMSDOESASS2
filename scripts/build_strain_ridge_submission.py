#!/usr/bin/env python3
"""Build the STRAIN-RIDGE submission: a unique, off-catalogue GeoTIFF.

Design (pre-registered in ``evidence/strain_ridge_run_card.json``):

* prior  = z(geodetic-strain + seismicity composite)
           + 0.5 * z(structure-tensor ridge of the LiDAR scarp stack)
* dots   = greedy blue-noise sample of the prior, minimum separation 3 cells
* mask   = hard 4-cell (400 m) collar around the COMPLETE official
           USGS/INGENIOUS fault database, plus the official NaN footprint
* budget = 35,000 cells, 1-cell emission

No competition label is read.  The catalogue is used only as a repeller.

Usage::

    python scripts/prepare_qfaults.py --shp /path/qfaults.shp \
        --sample data/bridge/sample_submission.tif --out-dir .cache/work
    GEMS_CUBE_NPZ=.cache/work/cube.npz \
    python scripts/build_strain_ridge_submission.py \
        --qfaults .cache/work/qfaults_100m.npy --sample data/bridge/sample_submission.tif \
        --labels data/bridge/labels.tif --out-dir docs/downloads --stem <stem>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.strain_ridge import (  # noqa: E402
    COLLAR_PX,
    MIN_SEP_PX,
    W_RIDGE,
    build_prior,
    collar_mask,
    dots_to_raster,
    greedy_dots,
)
from gems_sass2.submission import write_submission_pair  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cube", type=pathlib.Path, required=True,
                    help=".npz of the 32-layer feature cube on the competition grid")
    ap.add_argument("--qfaults", type=pathlib.Path, required=True,
                    help="bool .npy: complete official fault database on the grid")
    ap.add_argument("--sample", type=pathlib.Path, required=True)
    ap.add_argument("--labels", type=pathlib.Path, required=True)
    ap.add_argument("--out-dir", type=pathlib.Path, required=True)
    ap.add_argument("--stem", required=True)
    ap.add_argument("--n-dots", type=int, default=35_000)
    ap.add_argument("--w-ridge", type=float, default=W_RIDGE)
    ap.add_argument("--collar", type=float, default=COLLAR_PX)
    args = ap.parse_args()

    cube = {k: v for k, v in np.load(args.cube).items()}
    with rasterio.open(args.sample) as ds:
        footprint = np.isfinite(ds.read(1))
    faults = np.load(args.qfaults).astype(bool)

    prior = build_prior(cube, w_ridge=args.w_ridge)
    allowed = collar_mask(faults, args.collar) & footprint
    dots = greedy_dots(prior, allowed, args.n_dots, min_sep_px=MIN_SEP_PX)
    raster = dots_to_raster(dots, footprint.shape)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    receipt = write_submission_pair(raster, args.out_dir, args.stem,
                                    args.sample, args.labels)

    zeros = args.out_dir / f"{args.stem}-zeros.tif"
    sha = hashlib.sha256(zeros.read_bytes()).hexdigest()
    card = {
        "hypothesis": (
            "Active faults concentrate geodetic strain and seismicity, and their surface "
            "expression is a coherent topographic ridge; combining the two selects blind "
            "fault traces that the scarp-dependent USGS/INGENIOUS mapping missed."
        ),
        "mechanism": (
            "z(geod_2ndinv, geod_shearrate, ieq_n100a10) + 0.5*z(structure-tensor ridge of the "
            "LiDAR scarp stack) -> greedy blue-noise sample, 3-cell minimum separation, "
            "1-cell emission, hard 4-cell collar around the COMPLETE official fault database."
        ),
        "named_non_fault_process": (
            "Alluvial-fan toes and terrace risers produce coherent slope-excess ridges, and "
            "intraplate strain concentrates in basin axes without surface rupture; the "
            "400 m collar and the 3-cell separation damp but do not remove both mimics."
        ),
        "parameters": {
            "w_ridge": args.w_ridge, "min_sep_px": MIN_SEP_PX,
            "collar_px": args.collar, "n_dots": int(dots.size),
        },
        "raster_sha256": sha,
        "validator_output": receipt.get("zeros_validation", receipt),
        "submission_name": args.stem,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "promote",
    }
    (args.out_dir / f"{args.stem}-run-card.json").write_text(json.dumps(card, indent=2))

    print(json.dumps({
        "stem": args.stem,
        "n_dots": int(dots.size),
        "sha256": sha,
        "on_catalogue_cells": int((raster.astype(bool) & faults).sum()),
        "files": sorted(p.name for p in args.out_dir.glob(f"{args.stem}*")),
        "validation_all_passed": bool(receipt.get("zeros_validation", {}).get("all_passed")),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
