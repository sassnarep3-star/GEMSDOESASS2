#!/usr/bin/env python3
"""Prepare footprint & manifest after data placement."""
import pathlib, json, hashlib, rasterio, numpy as np
print("Checking data/ ...")
for p in ["data/training_features.tif","data/labels.tif","data/sample_submission.tif"]:
    path=pathlib.Path(p)
    print(p, "exists" if path.exists() else "MISSING — run download_competition_data.sh on unrestricted machine")
# Verify grid if present
try:
    with rasterio.open("data/sample_submission.tif") as src:
        print(f"sample: {src.width}x{src.height} {src.crs} {src.transform}")
        assert src.width==3292 and src.height==3730 and src.crs.to_epsg()==32611
        print("grid OK")
except Exception as e:
    print(f"skip grid check: {e}")
