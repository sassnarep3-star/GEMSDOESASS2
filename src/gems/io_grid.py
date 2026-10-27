"""Canonical competition grid I/O (verified against bridge files).

Grid: EPSG:32611, 3730 x 3292, 100 m pixels,
transform (100, 0, 243350, 0, -100, 4508550).
Footprint = finite pixels of sample_submission.tif (5,167,373 px).
"""
from __future__ import annotations

import hashlib
import os
import zipfile

import numpy as np
import rasterio
from rasterio.transform import Affine

GRID_SHAPE = (3730, 3292)
GRID_CRS = "EPSG:32611"
GRID_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIDGE = os.path.join(REPO, "data", "bridge")
REGISTRY_CACHE = os.environ.get(
    "GEMS_REGISTRY", os.path.expanduser("~/.cache/registry"))


def read_band(path: str, band: int = 1) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(band)


def load_bridge():
    faults = read_band(os.path.join(BRIDGE, "existing_faults.tif"))
    sample = read_band(os.path.join(BRIDGE, "sample_submission.tif"))
    footprint = np.isfinite(sample)
    catalogue = faults == 1
    return catalogue, footprint


def assert_grid(path: str):
    with rasterio.open(path) as ds:
        assert ds.shape == GRID_SHAPE, (path, ds.shape)
        assert str(ds.crs) == GRID_CRS, (path, ds.crs)
        t = ds.transform
        assert tuple(round(v, 6) for v in t[:6]) == tuple(GRID_TRANSFORM[:6]), (path, t)


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_submission(arr01: np.ndarray, out_tif: str, mode: str = "zeros",
                     footprint: np.ndarray | None = None) -> dict:
    """Write a float32 single-band GeoTIFF on the canonical grid.

    mode='zeros': every cell finite in [0,1] (0 outside footprint) --
    guaranteed to pass the portal check 'Predicted values must be in
    range [0, 1]'.  mode='nan': NaN outside footprint.
    """
    a = np.asarray(arr01, dtype=np.float32)
    assert a.shape == GRID_SHAPE
    inside = np.isfinite(a)
    if footprint is not None:
        bad = footprint & ~np.isfinite(a)
        if bad.any():
            raise ValueError(f"{int(bad.sum())} non-finite pixels inside footprint")
    if np.nanmin(a) < 0 or np.nanmax(a) > 1:
        raise ValueError("values outside [0,1]")
    out = a.copy()
    if mode == "zeros":
        out[~inside] = 0.0
        if footprint is not None:
            out[~footprint] = 0.0
        nodata = None
    elif mode == "nan":
        if footprint is not None:
            out[~footprint] = np.nan
        nodata = None
    else:
        raise ValueError(mode)
    profile = dict(driver="GTiff", height=GRID_SHAPE[0], width=GRID_SHAPE[1],
                   count=1, dtype="float32", crs=GRID_CRS,
                   transform=GRID_TRANSFORM, nodata=nodata,
                   compress="deflate", predictor=2, tiled=False)
    os.makedirs(os.path.dirname(out_tif), exist_ok=True)
    with rasterio.open(out_tif, "w", **profile) as ds:
        ds.write(out, 1)
    zpath = out_tif[:-4] + ".zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out_tif, os.path.basename(out_tif))
    return dict(tif=out_tif, zip=zpath, sha256=sha256(out_tif),
                size_bytes=os.path.getsize(out_tif))
