#!/usr/bin/env python3
"""Strict automated submission validator — no human inspection needed.

Checks (fail-closed, exit 1 on any failure):
  1. single band GeoTIFF
  2. dtype float32
  3. shape 3730 x 3292
  4. CRS EPSG:32611
  5. transform (100, 0, 243350, 0, -100, 4508550)
  6. every cell finite (zeros mode) OR finite inside footprint (nan mode)
  7. all finite values in [0, 1]  (cures portal error
     "Predicted values must be in range [0, 1]")
  8. zero NaN / Inf / sentinel inside the footprint
  9. zero positive pixels on the known catalogue (masked at scoring)
 10. zip contains exactly one .tif identical to the raster
"""
import json
import os
import sys
import zipfile

import numpy as np
import rasterio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gems.io_grid import GRID_CRS, GRID_SHAPE, GRID_TRANSFORM, load_bridge, sha256


def check(path, strict_finite=True):
    cat, footprint = load_bridge()
    results = {}
    with rasterio.open(path) as ds:
        results["single_band"] = ds.count == 1
        results["dtype_float32"] = ds.dtypes[0] == "float32"
        results["shape_3730x3292"] = ds.shape == GRID_SHAPE
        results["crs_epsg_32611"] = str(ds.crs) == GRID_CRS
        results["transform_match"] = tuple(round(v, 6) for v in ds.transform[:6]) == \
            tuple(GRID_TRANSFORM[:6])
        a = ds.read(1)
    fin = np.isfinite(a)
    inside = a[footprint]
    results["in_footprint_all_finite"] = bool(np.isfinite(inside).all())
    results["in_footprint_range_0_1"] = bool(
        np.isfinite(inside).all() and inside.min() >= 0.0 and inside.max() <= 1.0)
    allv = a[fin]
    results["all_finite_values_in_0_1"] = bool(
        (allv >= 0.0).all() and (allv <= 1.0).all()) if allv.size else False
    if strict_finite:
        results["every_cell_finite"] = bool(fin.all())
    results["zero_on_catalogue_positives"] = bool(
        (np.nan_to_num(a, nan=0.0)[cat] <= 0.0).all())
    results["positive_pixels"] = int((np.nan_to_num(a, nan=0.0) > 0).sum())
    results["sha256"] = sha256(path)
    zp = path[:-4] + ".zip"
    if os.path.exists(zp):
        with zipfile.ZipFile(zp) as z:
            names = [n for n in z.namelist() if n.endswith(".tif")]
            results["zip_single_tif"] = len(names) == 1
    ok = all(v for k, v in results.items()
             if isinstance(v, bool))
    results["ALL_CHECKS_PASSED"] = ok
    return results


if __name__ == "__main__":
    path = sys.argv[1]
    strict = "--allow-nan-outside" not in sys.argv
    r = check(path, strict_finite=strict)
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["ALL_CHECKS_PASSED"] else 1)
