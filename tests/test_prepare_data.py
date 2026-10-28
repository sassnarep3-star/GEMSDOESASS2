from __future__ import annotations

from pathlib import Path

from scripts.prepare_data import inspect


def test_prepare_data_fails_closed_when_core_files_are_missing(tmp_path: Path) -> None:
    receipt = inspect(tmp_path)
    assert receipt["status"] == "blocked"
    assert set(receipt["missing_required"]) == {
        "training_features.tif",
        "labels.tif",
        "sample_submission.tif",
    }
    assert "model run was started" in receipt["message"]
