#!/usr/bin/env python3
"""Automated validator - no human inspection. Usage: validate_submission.py file.tif sample_submission.tif"""
import sys, json, numpy as np, rasterio
path, tmpl = sys.argv[1], sys.argv[2]
checks={}
with rasterio.open(tmpl) as t: tp=t.profile
with rasterio.open(path) as ds:
    a=ds.read(1); p=ds.profile
    checks["single_band"]=ds.count==1
    checks["float32"]=str(a.dtype)=="float32"
    checks["shape_match"]=(ds.width,ds.height)==(tp["width"],tp["height"])
    checks["crs_epsg32611"]=ds.crs is not None and ds.crs.to_epsg()==32611
    checks["transform_match"]=tuple(ds.transform)==tuple(tp["transform"])
    checks["all_finite_no_nan"]=bool(np.isfinite(a).all())
    checks["values_in_0_1"]=bool(a.min()>=0.0 and a.max()<=1.0)
    checks["nodata_none"]=ds.nodata is None
    with rasterio.open(tmpl) as t: foot=np.isfinite(t.read(1))
    checks["no_positive_outside_footprint"]=bool((a[~foot]<=0).all())
    checks["dots_inside_footprint"]=int(((a>0)&foot).sum())
    checks["dots_total"]=int((a>0).sum())
    checks["min"],checks["max"]=float(a.min()),float(a.max())
checks["PASS"]=all(v for k,v in checks.items() if isinstance(v,bool))
print(json.dumps(checks,indent=2))
sys.exit(0 if checks["PASS"] else 1)
