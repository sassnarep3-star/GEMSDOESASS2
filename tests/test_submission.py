from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gemsdoesass2.integrity import inspect_template_label_relationship
from gemsdoesass2.submission import validate_submission, write_portal_safe_submission


def write_tif(path: Path, array: np.ndarray, *, nodata: float | None) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=array.shape[1],
        height=array.shape[0],
        count=1,
        dtype=str(array.dtype),
        crs="EPSG:32611",
        transform=from_origin(243350, 4508550, 100, 100),
        nodata=nodata,
    ) as dst:
        dst.write(array, 1)


def test_portal_safe_writer_zeros_template_nan_exterior(tmp_path: Path) -> None:
    template = np.full((6, 7), np.nan, dtype=np.float32)
    template[1:5, 1:6] = 0.0
    template_path = tmp_path / "template.tif"
    write_tif(template_path, template, nodata=np.nan)
    prediction = np.zeros((6, 7), dtype=np.float32)
    prediction[2, 3] = 0.75
    output = write_portal_safe_submission(prediction, template_path, tmp_path / "candidate.tif")
    report = validate_submission(output, template_path)
    assert report["format_valid"]
    with rasterio.open(output) as source:
        values = source.read(1)
        assert np.isfinite(values).all()
        assert values[0, 0] == 0.0
        assert source.nodata is None


def test_writer_rejects_nonfinite_inside_footprint(tmp_path: Path) -> None:
    template = np.ones((4, 4), dtype=np.float32)
    template_path = tmp_path / "template.tif"
    write_tif(template_path, template, nodata=None)
    prediction = np.zeros((4, 4), dtype=np.float32)
    prediction[1, 1] = np.nan
    try:
        write_portal_safe_submission(prediction, template_path, tmp_path / "bad.tif")
    except ValueError as error:
        assert "NaN" in str(error)
    else:
        raise AssertionError("writer accepted an invalid prediction")


def test_template_label_identity_is_flagged(tmp_path: Path) -> None:
    labels = np.full((5, 5), -1, dtype=np.int8)
    labels[1:4, 1:4] = 0
    labels[2, 2] = 1
    template = np.full((5, 5), np.nan, dtype=np.float32)
    template[1:4, 1:4] = (labels[1:4, 1:4] > 0).astype(np.float32)
    template_path = tmp_path / "template.tif"
    labels_path = tmp_path / "labels.tif"
    write_tif(template_path, template, nodata=np.nan)
    write_tif(labels_path, labels, nodata=-1)
    result = inspect_template_label_relationship(template_path, labels_path)
    assert result["exact_public_label_pattern_detected"]
    assert not result["promotion_gate_pass"]
