#!/usr/bin/env python3
"""Verify placement of the competition grid before any model run.

The DrivenData download is login-walled in this environment, so this command does
not pretend to download or authenticate it.  It verifies the three files needed
for the grid/label pipeline, checks their shared geometry, and writes a receipt.
The full SASS2 feature lane additionally needs the hash-pinned external files in
``registry/data_manifest.json`` and ``.cache/gems_data``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
REQUIRED = ("training_features.tif", "labels.tif", "sample_submission.tif")
OPTIONAL = ("1m_DEM_links.csv",)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def default_data_dir() -> Path:
    env = os.environ.get("GEMS_DATA_DIR")
    if env:
        return Path(env).expanduser()
    cache = ROOT / ".cache" / "gems_data"
    if cache.exists():
        return cache
    legacy = ROOT / ".cache" / "data"
    if legacy.exists():
        return legacy
    return ROOT / "data"


def inspect(data_dir: Path) -> dict:
    rows = []
    missing = []
    for name in REQUIRED + OPTIONAL:
        path = data_dir / name
        row = {"file": name, "exists": path.exists()}
        if path.exists():
            row.update({"bytes": path.stat().st_size, "sha256": sha256_file(path)})
        else:
            row["bytes"] = None
            row["sha256"] = None
            if name in REQUIRED:
                missing.append(name)
        rows.append(row)

    receipt: dict = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_dir": str(data_dir),
        "required_files": list(REQUIRED),
        "optional_files": list(OPTIONAL),
        "files": rows,
        "missing_required": missing,
        "geometry": None,
        "status": "blocked" if missing else "ready_for_geometry_checks",
    }
    if missing:
        receipt["message"] = (
            "Place the authenticated competition files in this directory or use "
            "scripts/fetch_data.py with a permitted hash-pinned mirror; no model run was started."
        )
        return receipt

    paths = {name: data_dir / name for name in REQUIRED}
    errors: list[str] = []
    with rasterio.open(paths["sample_submission.tif"]) as sample, rasterio.open(paths["labels.tif"]) as labels, rasterio.open(paths["training_features.tif"]) as features:
        sample_arr = sample.read(1)
        labels_arr = labels.read(1)
        geometry = {
            "sample_shape": list(sample.shape),
            "labels_shape": list(labels.shape),
            "features_shape": list(features.shape),
            "sample_crs": str(sample.crs),
            "labels_crs": str(labels.crs),
            "features_crs": str(features.crs),
            "sample_transform": list(sample.transform)[:6],
            "labels_transform": list(labels.transform)[:6],
            "features_transform": list(features.transform)[:6],
            "training_band_count": features.count,
            "footprint_pixels": int(np.isfinite(sample_arr).sum()),
            "label_finite_pixels": int(np.isfinite(labels_arr).sum()),
        }
        receipt["geometry"] = geometry
        if sample.shape != EXPECTED_SHAPE:
            errors.append(f"sample shape {sample.shape} != {EXPECTED_SHAPE}")
        if labels.shape != sample.shape or features.shape != sample.shape:
            errors.append("sample, labels, and training_features shapes do not match")
        for name, ds in (("sample", sample), ("labels", labels), ("features", features)):
            if str(ds.crs) != EXPECTED_CRS:
                errors.append(f"{name} CRS {ds.crs} != {EXPECTED_CRS}")
            transform = tuple(float(x) for x in ds.transform)[:6]
            if not np.allclose(transform, EXPECTED_TRANSFORM, atol=1e-6):
                errors.append(f"{name} transform does not match the 100 m EPSG:32611 grid")
        if features.count < 1:
            errors.append("training_features.tif has no bands")
        if not np.isfinite(labels_arr).all():
            errors.append("labels.tif contains NaN or Inf")

    receipt["geometry_errors"] = errors
    receipt["status"] = "geometry_failed" if errors else "grid_verified"
    receipt["message"] = (
        "Core grid is geometrically consistent; external feature restoration and authenticated-data provenance remain separate gates."
        if not errors
        else "Core files are present but geometry validation failed; no model run was started."
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=None, help="Directory containing competition core files")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence" / "prepare_data_receipt.json")
    args = parser.parse_args()
    data_dir = args.data_dir or default_data_dir()
    receipt = inspect(data_dir)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.receipt.with_suffix(args.receipt.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.receipt)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "grid_verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
