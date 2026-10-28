#!/usr/bin/env python3
"""Shared Competition Submission Writer & 13-Check Automated Validator (`submission_writer.py`).

Writes portal-safe `-zeros.tif` (`nodata=None`, all 12,279,160 cells finite `float32` in `[0,1]`),
archive GIS twin `-nan.tif`, single-file `.zip`, and deterministic `audit.json` receipt.
"""

from __future__ import annotations

# Fail closed: historical source is retained below for forensic review.
import sys as _legacy_sys
_LEGACY_REASON = 'Legacy writer is a private fork and cannot authorize or package a compliant submission.'
if __name__ == "__main__":
    print(_LEGACY_REASON + " DO NOT SUBMIT.", file=_legacy_sys.stderr)
    raise SystemExit(2)
raise RuntimeError(_LEGACY_REASON)

import argparse
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.paths import data_dir, downloads_dir  # noqa: E402
from gems_sass2.submission import validate_geotiff, write_submission_pair  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--validate-only", type=pathlib.Path, help="Validate an existing GeoTIFF on disk")
    ap.add_argument("--input-npy", type=pathlib.Path, help="2-D float32/bool array (.npy) to package as GeoTIFF pair")
    ap.add_argument("--stem", type=str, help="Output filename stem (without -zeros.tif)")
    ap.add_argument("--out-dir", type=pathlib.Path, default=None)
    args = ap.parse_args()

    ddir = data_dir()
    sub_p = ddir / "sample_submission.tif"
    lbl_p = ddir / "labels.tif"

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
