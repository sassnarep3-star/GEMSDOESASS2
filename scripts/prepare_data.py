#!/usr/bin/env python3
"""Validate local organizer data and build a disk-backed cached feature stack.

This script never downloads login-gated DrivenData data.  It requires files that
were already obtained through an authorized source and records only local hashes;
that is intentionally not a claim of organizer authentication.
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

from gemsdoesass2.integrity import inspect_template_label_relationship  # noqa: E402
from gemsdoesass2.io import assert_same_grid, sha256_file, template_footprint  # noqa: E402


def first_existing(paths: list[Path]) -> Path | None:
    return next((path for path in paths if path.is_file()), None)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--labels", type=Path, default=None)
    parser.add_argument("--features", type=Path, default=None)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data" / "cache" / "prepared")
    parser.add_argument("--no-copy-features", action="store_true", help="validate only; do not write feature_stack.npy")
    args = parser.parse_args()

    template = args.template or first_existing(
        [args.data_dir / "sample_submission.tif", args.data_dir / "example_submission.tif"]
    )
    labels = args.labels or first_existing(
        [args.data_dir / "labels.tif", args.data_dir / "existing_faults.tif"]
    )
    features = args.features or first_existing(
        [args.data_dir / "numeric_features.tif", args.data_dir / "gems-geodawn-numerical-features.tif"]
    )
    if not template or not labels or not features:
        missing = [name for name, value in (("template", template), ("labels", labels), ("features", features)) if value is None]
        raise SystemExit("Missing required local file(s): " + ", ".join(missing))
    assert_same_grid(template, labels, left_name="template", right_name="labels")
    assert_same_grid(template, features, left_name="template", right_name="numeric features")
    footprint, _, grid = template_footprint(template)
    with rasterio.open(features) as source:
        if source.count < 1:
            raise SystemExit("Feature raster has no bands")
        feature_count = source.count
        feature_dtype = source.dtypes[0]
        feature_tags = [source.tags(i) for i in range(1, source.count + 1)]
        feature_names = [tags.get("description", f"band_{index}") for index, tags in enumerate(feature_tags, start=1)]
        cache_path = args.cache_dir / "feature_stack.npy"
        if not args.no_copy_features:
            args.cache_dir.mkdir(parents=True, exist_ok=True)
            stack = np.lib.format.open_memmap(
                cache_path,
                mode="w+",
                dtype=np.float32,
                shape=(source.count, source.height, source.width),
            )
            for band in range(1, source.count + 1):
                stack[band - 1] = source.read(band, out_dtype="float32")
            stack.flush()
            del stack
    relationship = inspect_template_label_relationship(template, labels)
    manifest = {
        "schema": "gemsdoesass2-prepared-data-v1",
        "trust_status": "local hashes only; user must retain organizer download provenance separately",
        "template": {"path": str(template), "sha256": sha256_file(template)},
        "labels": {"path": str(labels), "sha256": sha256_file(labels)},
        "features": {
            "path": str(features),
            "sha256": sha256_file(features),
            "bands": feature_count,
            "dtype": feature_dtype,
            "names": feature_names,
            "cache": str(args.cache_dir / "feature_stack.npy") if not args.no_copy_features else None,
        },
        "grid": {"shape": list(grid.shape), "crs_wkt": grid.crs_wkt, "transform": list(grid.transform)[:6], "footprint_pixels": int(footprint.sum())},
        "template_label_integrity": relationship,
    }
    args.cache_dir.mkdir(parents=True, exist_ok=True)
    output = args.cache_dir / "prepared_manifest.json"
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    # Equality is a serious input integrity warning but should not prevent a user
    # from preserving the diagnostic manifest.  Promotion is blocked downstream.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
