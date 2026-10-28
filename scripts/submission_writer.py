#!/usr/bin/env python3
"""Shared Competition Submission Writer & 13-Check Automated Validator (`submission_writer.py`).

Writes portal-safe `-zeros.tif` (`nodata=None`, all 12,279,160 cells finite `float32` in `[0,1]`),
archive GIS twin `-nan.tif`, single-file `.zip`, and deterministic `audit.json` receipt.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.paths import downloads_dir, grid_data_dir  # noqa: E402
from gems_sass2.submission import validate_geotiff, write_submission_pair  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-only", type=pathlib.Path, help="Validate an existing GeoTIFF on disk")
    ap.add_argument("--input-npy", type=pathlib.Path, help="2-D float32/bool array (.npy) to package as GeoTIFF pair")
    ap.add_argument("--stem", type=str, help="Output filename stem (without -zeros.tif)")
    ap.add_argument("--out-dir", type=pathlib.Path, default=None)
    ap.add_argument(
        "--sample",
        type=pathlib.Path,
        default=None,
        help="Grid template; defaults to the restored cache or tracked data/bridge mirror",
    )
    ap.add_argument(
        "--labels",
        type=pathlib.Path,
        default=None,
        help="Catalogue labels; defaults next to --sample",
    )
    args = ap.parse_args()

    grid_dir = grid_data_dir()
    sub_p = args.sample or (grid_dir / "sample_submission.tif")
    lbl_p = args.labels or (sub_p.parent / "labels.tif")
    if not sub_p.exists() or not lbl_p.exists():
        ap.error(
            "No sample/labels pair found. Place the authenticated competition grid in "
            "the restored cache or pass --sample and --labels explicitly."
        )

    if args.validate_only is not None:
        strict = not args.validate_only.name.endswith("-nan.tif")
        res = validate_geotiff(args.validate_only, sub_p, lbl_p, strict_all_finite=strict)
        print(json.dumps(res, indent=2))
        return 0 if res["all_passed"] else 1

    if args.input_npy is None or not args.stem:
        ap.error("Provide --validate-only OR (--input-npy and --stem)")

    arr = np.load(args.input_npy)
    odir = args.out_dir or downloads_dir()
    receipt = write_submission_pair(arr, odir, args.stem, sub_p, lbl_p)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
