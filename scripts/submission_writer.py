#!/usr/bin/env python3
"""Write a strict portal-safe single-band GeoTIFF from an aligned .npy prediction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.submission import validate_submission, write_portal_safe_submission  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prediction", type=Path, help="2-D NumPy .npy prediction array")
    parser.add_argument("output", type=Path, help="Output .tif path")
    parser.add_argument("--template", type=Path, required=True)
    args = parser.parse_args()
    prediction = np.load(args.prediction, allow_pickle=False)
    output = write_portal_safe_submission(prediction, args.template, args.output)
    report = validate_submission(output, args.template)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["format_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
