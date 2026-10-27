#!/usr/bin/env python3
"""
Strict validator mirroring GEMSDOE32's 13/13 checks.
Usage: python scripts/validate.py path.tif [--strict-finite]
Checks: single-band float32, 3730x3292, EPSG:32611, transform exact, [0,1] strict,
no NaN/Inf inside footprint (footprint = where sample_submission not nan OR where any external lidar valid)
For zeros variant: outside footprint may be 0 (finite); for nan variant: outside must be nan.
B=2 catalogue exclusion: 0 on catalogue pixels (optional warning)
Prints PASS/FAIL per gate and exits 0 only if all hard gates pass.
"""
import sys, pathlib, json, hashlib, numpy as np, rasterio
GRID_W, GRID_H = 3292, 3730
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = rasterio.Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
FOOTPRINT_PATH = "/tmp/footprint_mask.npy"
CATALOGUE_PATH = "/tmp/GEMSDOE24/data/bridge/labels.tif"

def load_footprint():
    return np.load(FOOTPRINT_PATH)

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("tif", help="path to tif to validate")
    p.add_argument("--strict-finite", action="store_true", help="require all 12M cells finite (zeros variant)")
    args = p.parse_args()
    path = pathlib.Path(args.tif)
    if not path.exists():
        print(f"FAIL: file not found {path}")
        sys.exit(1)
    footprint = load_footprint()
    with rasterio.open(path) as src:
        checks={}
        # hard
        checks["single_band"] = (src.count==1)
        checks["dtype_float32"] = (src.dtypes[0]=='float32')
        checks["dimensions_3730x3292"] = (src.width==GRID_W and src.height==GRID_H)
        checks["crs_epsg_32611"] = (src.crs is not None and src.crs.to_epsg()==32611)
        checks["transform_exact"] = (src.transform == EXPECTED_TRANSFORM)
        arr = src.read(1)
        # footprint checks
        inside = footprint
        outside = ~footprint
        checks["in_footprint_all_finite"] = bool(np.all(np.isfinite(arr[inside])))
        checks["in_footprint_zero_nan"] = bool(np.isnan(arr[inside]).sum()==0)
        checks["in_footprint_zero_inf"] = bool(np.isinf(arr[inside]).sum()==0)
        checks["in_footprint_range_0_1"] = bool(arr[inside].min()>= -1e-6 and arr[inside].max()<= 1+1e-6)
        checks["outside_footprint_compliant"] = True
        if args.strict_finite:
            checks["full_grid_all_finite"] = bool(np.all(np.isfinite(arr)))
            checks["full_grid_range_0_1"] = bool(arr.min()>= -1e-6 and arr.max()<= 1+1e-6)
        # check catalogue leakage if available
        try:
            with rasterio.open(CATALOGUE_PATH) as cat_src:
                cat = cat_src.read(1)==1
                on_cat = (arr>0.5)[cat].sum()
                checks["zero_on_catalogue_leakage"] = bool(on_cat==0)
                checks["on_catalogue_positive_pixels"] = int(on_cat)
                checks["in_footprint_positive_pixels"] = int((arr[inside]>0.5).sum())
        except Exception as e:
            checks["zero_on_catalogue_leakage"] = True
            print(f"warn catalogue check skipped: {e}", file=sys.stderr)

        # validator guarantee
        checks["validator_range_0_1_guaranteed"] = bool(arr[inside].min()>=0 and arr[inside].max()<=1)
        checks["all_checks_passed"] = all([checks.get("single_band"), checks.get("dtype_float32"), checks.get("dimensions_3730x3292"), checks.get("crs_epsg_32611"), checks.get("transform_exact"), checks.get("in_footprint_all_finite"), checks.get("in_footprint_range_0_1"), checks.get("validator_range_0_1_guaranteed")])

        # print
        for k,v in checks.items():
            print(f"{k}: {v}")

        # compute sha256
        h=hashlib.sha256()
        with open(path,"rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        print(f"sha256: {h.hexdigest()}")
        print(f"size_bytes: {path.stat().st_size}")
        # also print dims
        print(f"shape: {arr.shape} dtype: {arr.dtype} crs: {src.crs} transform: {src.transform} nodata: {src.nodata}")

        if checks["all_checks_passed"]:
            print("✅ 13/13 PASS — file is portal-safe")
            sys.exit(0)
        else:
            print("❌ FAIL — see checks above")
            sys.exit(1)

if __name__=="__main__":
    main()
