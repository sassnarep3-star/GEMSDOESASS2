#!/usr/bin/env python3
"""Fetch the nine pinned peer rasters and verify SHA-256 before novelty checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.registry import fetch_registry  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "registry" / "focus_registry.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "registry_rasters")
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args()
    receipt = fetch_registry(args.manifest, args.output_dir)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text)
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
