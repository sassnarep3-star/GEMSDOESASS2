"""Regression tests for the fail-closed packaging boundary.

These tests protect the two user-visible failure modes found during the repo review:
missing-data path ambiguity and silently clipped invalid prediction values.
"""
from __future__ import annotations

import numpy as np
import pytest

from gems_sass2.paths import EXPECTED_SHAPE, REPO_ROOT, grid_data_dir
from gems_sass2.submission import write_submission_pair


def test_grid_inspection_falls_back_to_tracked_bridge(monkeypatch, tmp_path) -> None:
    """A clean checkout can inspect the committed witness without using /tmp paths."""
    monkeypatch.setenv("GEMS_DATA_DIR", str(tmp_path / "does-not-exist"))
    assert grid_data_dir() == REPO_ROOT / "data" / "bridge"


@pytest.mark.parametrize(
    "bad_value, message",
    [
        (np.nan, "NaN or Inf"),
        (np.inf, "NaN or Inf"),
        (-np.float32(1e-6), "outside"),
        (np.float32(1.000001), "outside"),
    ],
)
def test_writer_rejects_invalid_values_before_creating_files(tmp_path, bad_value, message) -> None:
    pred = np.zeros(EXPECTED_SHAPE, dtype=np.float32)
    pred[0, 0] = bad_value
    with pytest.raises(ValueError, match=message):
        write_submission_pair(
            pred,
            tmp_path,
            "invalid",
            REPO_ROOT / "data" / "bridge" / "sample_submission.tif",
            REPO_ROOT / "data" / "bridge" / "labels.tif",
        )
    assert not list(tmp_path.iterdir()), "invalid predictions must not leave partial output"
