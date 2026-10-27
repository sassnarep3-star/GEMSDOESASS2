from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from scripts.validate_tif import validate


def write(path: Path, array, *, transform=None, crs="EPSG:32611", nodata=None, mask=None):
    arrays = np.asarray(array, dtype=np.float32)
    if arrays.ndim == 2:
        arrays = arrays[None, ...]
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(
            path, "w", driver="GTiff", width=arrays.shape[2], height=arrays.shape[1], count=arrays.shape[0],
            dtype="float32", crs=crs, transform=transform or from_origin(100, 500, 100, 100), nodata=nodata,
        ) as ds:
            ds.write(arrays)
            if mask is not None:
                ds.write_mask(np.asarray(mask, dtype=np.uint8) * 255)
    return path


@pytest.fixture
def rasters(tmp_path):
    foot = np.array([[0, 1, 1], [0, 1, 1], [0, 1, 1]], dtype=bool)
    sample = write(tmp_path / "sample.tif", np.where(foot, 0.0, np.nan), nodata=np.nan)
    return tmp_path, sample, foot


def test_masked_finite_pixels_can_satisfy_both_local_checks(rasters):
    root, sample, foot = rasters
    out = write(root / "candidate.tif", np.where(foot, .4, 0), mask=foot)
    r = validate(out, sample)
    assert r["strict_local_format_pass"]
    assert r["counts"]["inside_nan"] == 0
    assert r["organizer_accepted"] is None
    assert r["ok_to_submit"] is False


@pytest.mark.parametrize("bad", [np.nan, np.inf, -1, 1.01])
def test_rejects_nonfinite_and_out_of_range_inside(rasters, bad):
    root, sample, foot = rasters
    a = np.zeros((3, 3), dtype=np.float32); a[1, 1] = bad
    out = write(root / "bad.tif", a, mask=foot)
    r = validate(out, sample)
    assert not r["strict_local_format_pass"]
    assert not r["checks"]["inside_unmasked_finite_in_0_1"]
    assert not r["checks"]["whole_array_finite_in_0_1"]


def test_fails_closed_on_unmasked_outside(rasters):
    root, sample, _ = rasters
    out = write(root / "unmasked.tif", np.zeros((3, 3)))
    r = validate(out, sample)
    assert r["checks"]["whole_array_finite_in_0_1"]
    assert not r["checks"]["outside_masked_or_nan"]
    assert not r["strict_local_format_pass"]


def test_masked_inside_is_not_valid(rasters):
    root, sample, foot = rasters
    mask = foot.copy(); mask[1, 1] = False
    out = write(root / "missing.tif", np.zeros((3, 3)), mask=mask)
    assert validate(out, sample)["counts"]["inside_masked"] == 1
    assert not validate(out, sample)["strict_local_format_pass"]


def test_nan_outside_meets_null_but_not_strict_whole_array_policy(rasters):
    root, sample, foot = rasters
    out = write(root / "outside-nan.tif", np.where(foot, .5, np.nan), nodata=np.nan)
    r = validate(out, sample)
    assert r["checks"]["outside_masked_or_nan"]
    assert not r["checks"]["whole_array_finite_in_0_1"]
    assert not r["strict_local_format_pass"]


@pytest.mark.parametrize("change", ["shape", "transform", "crs", "bands", "extension"])
def test_rejects_grid_and_contract_mismatches(rasters, change):
    root, sample, foot = rasters
    kwargs = {"mask": foot}
    data = np.zeros((3, 3), dtype=np.float32)
    path = root / ("candidate.tiff" if change == "extension" else "candidate.tif")
    if change == "shape":
        data = np.zeros((2, 3), dtype=np.float32); kwargs["mask"] = foot[:2]
    if change == "transform": kwargs["transform"] = from_origin(101, 500, 100, 100)
    if change == "crs": kwargs["crs"] = "EPSG:4326"
    if change == "bands": data = np.stack([data, data])
    result = validate(write(path, data, **kwargs), sample)
    assert not result["strict_local_format_pass"]


def test_matching_wrong_reference_cannot_bypass_official_crs_or_resolution(tmp_path):
    wrong_transform = from_origin(100, 500, 50, 50)
    sample = write(tmp_path / 'sample.tif', np.zeros((3, 3)), transform=wrong_transform, crs='EPSG:4326')
    candidate = write(tmp_path / 'candidate.tif', np.zeros((3, 3)), transform=wrong_transform, crs='EPSG:4326')
    result = validate(candidate, sample)
    assert result['checks']['crs_match'] and result['checks']['transform_match']
    assert not result['checks']['competition_crs_epsg32611']
    assert not result['checks']['competition_100m_north_up']
    assert not result['strict_local_format_pass']
