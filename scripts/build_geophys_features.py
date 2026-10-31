#!/usr/bin/env python3
"""Build (or verify) the multi-scale structural feature cube from the official stack.

Usage
-----
    python scripts/build_geophys_features.py [--force]

Writes `.cache/features/clean_stack.npy` (19-band, inpainted, z-scored) and
`.cache/features/feature_cube.npy` (83 structural features).  Both are
disk-backed memmaps and are never committed; `scripts/fetch_training_features.sh`
reproduces the source raster from a hash-pinned public GitHub repository.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import geophys  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src = geophys.stack_path(ROOT)
    if not src.exists():
        print(f"missing {src}; run scripts/fetch_training_features.sh", file=sys.stderr)
        return 2

    cube_path = ROOT / ".cache" / "features" / "feature_cube.npy"
    names = geophys.feature_names()
    if cube_path.exists() and not args.force:
        with open(cube_path, "rb") as fh:
            version = np.lib.format.read_magic(fh)
            shape, _, dtype = np.lib.format._read_array_header(fh, version)
        print(f"cube already present: shape={shape} dtype={dtype} features={len(names)}")
        return 0

    cube, coverage, names = geophys.build_feature_cube(ROOT)
    summary = {
        "source": str(src),
        "source_sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
        "features": names,
        "n_features": len(names),
        "shape": list(coverage.shape),
        "coverage_pixels": int(coverage.sum()),
        "coverage_fraction": float(coverage.mean()),
        "scales_gauss": list(geophys.SCALES),
        "scales_gradient": list(geophys.GRAD_SCALES),
        "label_derived_inputs": [],
        "note": "No catalogue/label raster is read by this stage; features are geophysics only.",
    }
    out = ROOT / "evidence" / "geophys_feature_cube.json"
    out.write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "features"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
