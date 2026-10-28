"""13-Check GeoTIFF Submission Writer & Automated Saved-Byte Validator.

Fixes shared template issue `IR-TEMPLATE-NODATA-01`:
  - Primary deliverable (`-zeros.tif`) writes `nodata=None` with all `12,279,160` cells
    strictly finite `float32` in `[0.0, 1.0]` (`0.0` outside footprint, `0.0` on all
    `60,988` `labels.tif` catalogue pixels), matching `drivendataorg/gems-prize-reference-solution`
    Cell 19 and permanently preventing DrivenData's `"Predicted values must be in range [0, 1]"`
    portal rejection.
  - Companion archive twin (`-nan.tif`) writes `np.nan` outside the `5,167,373`-pixel footprint
    for visual GIS inspection.
"""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from .paths import (
    EXPECTED_CATALOGUE_POSITIVES,
    EXPECTED_CRS,
    EXPECTED_FOOTPRINT_PIXELS,
    EXPECTED_HEIGHT,
    EXPECTED_SHAPE,
    EXPECTED_TRANSFORM,
    EXPECTED_WIDTH,
)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_geotiff(
    tif_path: str | Path,
    sample_submission_path: str | Path,
    labels_path: str | Path,
    strict_all_finite: bool = True,
) -> dict:
    """Run all 13 deterministic automated checks directly on saved GeoTIFF bytes."""
    tif_path = Path(tif_path)
    with rasterio.open(sample_submission_path) as ds_sub:
        foot = np.isfinite(ds_sub.read(1))
        sub_crs = str(ds_sub.crs)
        sub_shape = ds_sub.shape
        sub_transform = tuple(float(x) for x in ds_sub.transform)[:6]

    with rasterio.open(labels_path) as ds_lbl:
        known = (ds_lbl.read(1) >= 1) & foot

    with rasterio.open(tif_path) as ds:
        arr = ds.read(1)
        mask_arr = ds.dataset_mask() > 0
        crs = str(ds.crs)
        shape = ds.shape
        count = ds.count
        dtype = ds.dtypes[0]
        nodata = ds.nodata
        transform = tuple(float(x) for x in ds.transform)[:6]

    in_vals = arr[foot]
    out_vals = arr[~foot]
    cat_vals = arr[known]

    finite_in = bool(np.isfinite(in_vals).all())
    finite_all = bool(np.isfinite(arr).all())
    in_min = float(np.nanmin(in_vals)) if in_vals.size else 0.0
    in_max = float(np.nanmax(in_vals)) if in_vals.size else 0.0
    all_min = float(np.nanmin(arr))
    all_max = float(np.nanmax(arr))
    out_ok_zeros = bool(np.isfinite(out_vals).all() and np.all(out_vals == 0.0))
    out_ok_nan = bool(np.isnan(out_vals).all())
    mask_exact_foot = bool(mask_arr.shape == foot.shape and np.array_equal(mask_arr, foot))
    on_cat_pos = int((np.isfinite(cat_vals) & (cat_vals > 0.0)).sum())
    n_pos_in_foot = int((np.isfinite(in_vals) & (in_vals > 0.0)).sum())

    checks = {
        "01_file_exists_nonempty": tif_path.exists() and tif_path.stat().st_size > 1024,
        "02_single_band": count == 1,
        "03_dtype_float32": dtype == "float32",
        "04_crs_epsg_32611": crs == EXPECTED_CRS == sub_crs,
        "05_shape_3730x3292": shape == EXPECTED_SHAPE == sub_shape,
        "06_geotransform_exact": np.allclose(transform, EXPECTED_TRANSFORM, atol=1e-6)
        and np.allclose(transform, sub_transform, atol=1e-6),
        "07_footprint_5167373_match": int(foot.sum()) == EXPECTED_FOOTPRINT_PIXELS,
        "08_catalogue_60988_match": int(known.sum()) == EXPECTED_CATALOGUE_POSITIVES,
        "09_no_nan_or_inf_inside_footprint": finite_in,
        "10_values_in_0_1_inside_footprint": finite_in and (in_min >= 0.0) and (in_max <= 1.0),
        "11_outside_footprint_clean": (out_ok_zeros and mask_exact_foot) if strict_all_finite else (out_ok_zeros or out_ok_nan),
        "12_zero_on_known_catalogue": on_cat_pos == 0,
        "13_nontrivial_positive_predictions": n_pos_in_foot > 0,
    }
    passed = sum(1 for v in checks.values() if v)
    return {
        "path": str(tif_path),
        "filename": tif_path.name,
        "size_bytes": int(tif_path.stat().st_size),
        "sha256": sha256_file(tif_path),
        "crs": crs,
        "shape": [int(shape[0]), int(shape[1])],
        "dtype": dtype,
        "nodata": None if nodata is None else ( "NaN" if np.isnan(nodata) else float(nodata) ),
        "transform": list(transform),
        "all_12279160_finite": finite_all,
        "min_in_footprint": in_min,
        "max_in_footprint": in_max,
        "min_all_cells": all_min,
        "max_all_cells": all_max,
        "positive_dots_in_footprint": n_pos_in_foot,
        "positive_on_catalogue": on_cat_pos,
        "outside_mode": "zeros" if out_ok_zeros else ("nan" if out_ok_nan else "mixed"),
        "checks": checks,
        "checks_passed": passed,
        "checks_total": len(checks),
        "all_passed": passed == len(checks),
    }


def write_submission_pair(
    pred_values: np.ndarray,
    out_dir: str | Path,
    stem: str,
    sample_submission_path: str | Path,
    labels_path: str | Path,
) -> dict:
    """Write `-zeros.tif` (primary portal-safe), `-nan.tif` (GIS twin), and `.zip`, then verify saved bytes."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with rasterio.open(sample_submission_path) as ds_sub:
        foot = np.isfinite(ds_sub.read(1))
        profile = ds_sub.profile.copy()
    with rasterio.open(labels_path) as ds_lbl:
        known = (ds_lbl.read(1) >= 1) & foot

    arr = np.asarray(pred_values, dtype=np.float32)
    if arr.shape != EXPECTED_SHAPE:
        raise ValueError(f"Expected shape {EXPECTED_SHAPE}, got {arr.shape}")
    # Do not silently repair model output here.  Clipping NaN, Inf, or a value
    # just above one can hide the exact bug that later triggers the portal's
    # ``Predicted values must be in range [0, 1]`` rejection.  Probability
    # calibration belongs upstream; the packaging boundary is fail-closed.
    if not np.isfinite(arr).all():
        raise ValueError("Prediction array contains NaN or Inf; nothing was written")
    arr_min = float(arr.min())
    arr_max = float(arr.max())
    if arr_min < 0.0 or arr_max > 1.0:
        raise ValueError(
            f"Prediction array is outside [0, 1] (min={arr_min:.9g}, max={arr_max:.9g}); "
            "calibrate it before packaging"
        )
    arr = arr.astype(np.float32, copy=True)
    arr[known] = np.float32(0.0)

    zeros_arr = np.where(foot, arr, np.float32(0.0)).astype(np.float32)
    nan_arr = np.where(foot, arr, np.float32(np.nan)).astype(np.float32)

    zeros_path = out_dir / f"{stem}-zeros.tif"
    nan_path = out_dir / f"{stem}-nan.tif"
    zip_path = out_dir / f"{stem}-zeros.zip"

    prof_zeros = {
        "driver": "GTiff",
        "height": EXPECTED_HEIGHT,
        "width": EXPECTED_WIDTH,
        "count": 1,
        "dtype": "float32",
        "crs": profile["crs"],
        "transform": profile["transform"],
        "nodata": None,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(zeros_path, "w", **prof_zeros) as dst:
            dst.write(zeros_arr, 1)
            dst.write_mask(foot.astype(np.uint8) * 255)

    prof_nan = dict(prof_zeros, nodata=np.nan, predictor=1)
    with rasterio.open(nan_path, "w", **prof_nan) as dst:
        dst.write(nan_arr, 1)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)

    val_zeros = validate_geotiff(zeros_path, sample_submission_path, labels_path, strict_all_finite=True)
    val_nan = validate_geotiff(nan_path, sample_submission_path, labels_path, strict_all_finite=False)
    if not val_zeros["all_passed"]:
        raise RuntimeError(f"Primary zeros GeoTIFF failed validation: {val_zeros}")
    if not val_nan["all_passed"]:
        raise RuntimeError(f"Archive nan GeoTIFF failed validation: {val_nan}")

    return {
        "stem": stem,
        "zeros": val_zeros,
        "nan": val_nan,
        "zip": {
            "path": str(zip_path),
            "filename": zip_path.name,
            "size_bytes": int(zip_path.stat().st_size),
            "sha256": sha256_file(zip_path),
        },
    }
