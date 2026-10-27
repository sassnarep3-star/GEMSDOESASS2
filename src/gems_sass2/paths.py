"""Canonical paths and competition grid constants for GEMSDOESASS2."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import rasterio

REPO_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_CRS = "EPSG:32611"
EXPECTED_HEIGHT = 3730
EXPECTED_WIDTH = 3292
EXPECTED_SHAPE = (EXPECTED_HEIGHT, EXPECTED_WIDTH)
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_FOOTPRINT_PIXELS = 5_167_373
EXPECTED_CATALOGUE_POSITIVES = 60_988
NODATA_SENTINEL_F32 = np.float32(-3.4028234663852886e38)


def data_dir() -> Path:
    env = os.environ.get("GEMS_DATA_DIR")
    if env:
        return Path(env)
    cand = REPO_ROOT / ".cache" / "data"
    if cand.exists():
        return cand
    return Path("/tmp/gems_data")


def work_dir() -> Path:
    env = os.environ.get("GEMS_WORK_DIR")
    if env:
        p = Path(env)
    else:
        p = REPO_ROOT / ".cache" / "work"
    p.mkdir(parents=True, exist_ok=True)
    return p


def downloads_dir() -> Path:
    p = REPO_ROOT / "docs" / "downloads"
    p.mkdir(parents=True, exist_ok=True)
    return p


def evidence_dir() -> Path:
    p = REPO_ROOT / "evidence"
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_footprint_and_catalogue(ddir: Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load exact 5,167,373-pixel footprint and 60,988-pixel catalogue mask."""
    ddir = ddir or data_dir()
    sub_p = ddir / "sample_submission.tif"
    lbl_p = ddir / "labels.tif"
    with rasterio.open(sub_p) as ds_sub:
        foot = np.isfinite(ds_sub.read(1))
    with rasterio.open(lbl_p) as ds_lbl:
        lbl_raw = ds_lbl.read(1)
        known = (lbl_raw >= 1) & foot
    if int(foot.sum()) != EXPECTED_FOOTPRINT_PIXELS:
        raise ValueError(f"Footprint count {int(foot.sum())} != {EXPECTED_FOOTPRINT_PIXELS}")
    if int(known.sum()) != EXPECTED_CATALOGUE_POSITIVES:
        raise ValueError(f"Catalogue positives {int(known.sum())} != {EXPECTED_CATALOGUE_POSITIVES}")
    return foot, known
