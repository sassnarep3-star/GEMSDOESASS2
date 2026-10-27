from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "docs" / "downloads"
CARD = ROOT / "docs" / "data" / "cdcc_20261027_run_card.json"


def test_checked_in_research_tif_matches_run_card_and_is_quarantined() -> None:
    card = json.loads(CARD.read_text())
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert card["submission"]["note_characters"] <= 140
    tif = DOWNLOADS / card["submission"]["file"]
    assert "RESEARCH-DO-NOT-SUBMIT" in tif.name
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    with rasterio.open(tif) as source:
        values = source.read(1)
        assert source.count == 1
        assert source.dtypes == ("float32",)
        assert np.isfinite(values).all()
        assert np.all((values >= 0.0) & (values <= 1.0))
        assert int((values > 0).sum()) == card["submission"]["dot_count"]


def test_checked_in_zip_contains_only_the_recorded_tif_bytes() -> None:
    card = json.loads(CARD.read_text())
    tif = DOWNLOADS / card["submission"]["file"]
    archive_path = DOWNLOADS / card["submission"]["zip"]
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == [tif.name]
        assert archive.read(tif.name) == tif.read_bytes()
