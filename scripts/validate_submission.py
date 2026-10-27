#!/usr/bin/env python3
"""Validate a candidate GeoTIFF against a local submission template."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.submission import save_validation_report, validate_submission  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    report = validate_submission(args.submission, args.template)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        save_validation_report(report, args.report)
    return 0 if report["format_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
