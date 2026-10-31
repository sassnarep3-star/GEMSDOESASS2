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


def test_zeros_outside_is_an_accepted_encoding(rasters):
    """IR-31-01. The old rule (`all(checks.values())`) rejected a file that is finite
    and inside [0,1] everywhere merely because its outside values are 0.0 rather than
    NaN -- even though that is what the organizer sample and every top submission ship,
    and even though the portal's "[0,1]" check cannot fire on it. The strict pass now
    requires ONE valid outside-bounds encoding, and this is one of them."""
    root, sample, _ = rasters
    out = write(root / "unmasked.tif", np.zeros((3, 3)))
    r = validate(out, sample)
    assert r["checks"]["whole_array_finite_in_0_1"]
    assert not r["checks"]["outside_masked_or_nan"]
    assert r["strict_local_format_pass"] is True
    assert r["outside_bounds_encoding"] == "zeros_finite_outside"
    assert r["portal_range_safe"] is True
    assert r["organizer_accepted"] is None
    assert r["ok_to_submit"] is False


@pytest.mark.parametrize("bad_outside", [0.5, 1.0, 2.0, -1.0])
def test_fails_closed_on_nonzero_outside_values(rasters, bad_outside):
    """Equal-or-stronger replacement for the old `unmasked outside == fail` rule: a
    file that *predicts* outside the footprint fails whatever its range."""
    root, sample, foot = rasters
    a = np.zeros((3, 3), dtype=np.float32)
    a[~foot] = bad_outside
    r = validate(write(root / "outside-nonzero.tif", a), sample)
    assert not r["strict_local_format_pass"]
    assert r["counts"]["outside_all_zero"] is False
    # 0.5 outside is finite and in range, so the [0,1] check alone must not rescue it
    assert r["outside_bounds_encoding"] in ("nonzero_finite_outside", "INVALID")


def test_masked_inside_is_not_valid(rasters):
    root, sample, foot = rasters
    mask = foot.copy(); mask[1, 1] = False
    out = write(root / "missing.tif", np.zeros((3, 3)), mask=mask)
    assert validate(out, sample)["counts"]["inside_masked"] == 1
    assert not validate(out, sample)["strict_local_format_pass"]


def test_nan_outside_passes_but_is_not_portal_range_safe(rasters):
    """IR-31-01. NaN outside satisfies the published spec ("null or nan"), so it is a
    valid encoding and the strict pass accepts it -- but it is flagged
    `portal_range_safe: False`, because the portal's validation is unpublished and the
    reported rejection was "Predicted values must be in range [0, 1]". Ship the zeros
    twin."""
    root, sample, foot = rasters
    out = write(root / "outside-nan.tif", np.where(foot, .5, np.nan), nodata=np.nan)
    r = validate(out, sample)
    assert r["checks"]["outside_masked_or_nan"]
    assert not r["checks"]["whole_array_finite_in_0_1"]
    assert r["strict_local_format_pass"] is True
    assert r["outside_bounds_encoding"] == "masked_or_nan_outside"
    assert r["portal_range_safe"] is False


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
