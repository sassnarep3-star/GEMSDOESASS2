#!/usr/bin/env python3
"""Shared whole-segment HOLDOUT-DTI evaluator for an aligned static surface.

The script does not fit a model and does not spend a submission slot. It is the
reusable evaluator called conceptually by experiment runners; use it to audit a
saved pre-placement surface independently of TIFF packaging.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.holdout import evaluate_surface, leakage_canary, make_segment_holdout, strip_internal_arrays  # noqa: E402
from gemsdoesass2.io import assert_same_grid, template_footprint  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--surface", type=Path, required=True, help="Aligned 2-D .npy static surface")
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--budget", type=int, default=37_654)
    parser.add_argument("--bootstrap-draws", type=int, default=2_000)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    if args.budget <= 0 or args.bootstrap_draws < 100:
        raise SystemExit("budget must be positive and bootstrap-draws at least 100")
    assert_same_grid(args.template, args.labels, left_name="template", right_name="labels")
    footprint, _, grid = template_footprint(args.template)
    with rasterio.open(args.labels) as source:
        labels = (source.read(1) > 0) & footprint
    surface = np.load(args.surface, allow_pickle=False)
    holdout = make_segment_holdout(footprint, labels, buffer_px=3)
    canary = leakage_canary(holdout, {"surface": surface})
    result = evaluate_surface(
        holdout,
        surface,
        pixel_size_m=abs(grid.transform.a),
        budget=args.budget,
        n_bootstraps=args.bootstrap_draws,
    )
    payload = {
        "canary": canary,
        "holdout": strip_internal_arrays(result),
        "submission_slot_spent": False,
        "scope": "Local proxy HOLDOUT-DTI only; not an organizer score or submission authorization.",
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
    return 0 if canary["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
