"""Raster and checksum primitives shared by every experiment.

The helpers deliberately validate grid identity rather than silently reprojecting:
a silent resample would invalidate a competition submission and a novelty audit.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from affine import Affine


@dataclass(frozen=True)
class Grid:
    """The immutable spatial properties a submission must inherit from its template."""

    shape: tuple[int, int]
    crs_wkt: str | None
    transform: Affine

    @classmethod
    def from_dataset(cls, dataset: rasterio.io.DatasetReader) -> "Grid":
        return cls(
            shape=dataset.shape,
            crs_wkt=dataset.crs.to_wkt() if dataset.crs is not None else None,
            transform=dataset.transform,
        )


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a content SHA-256 without loading the entire artifact into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def content_id(array: np.ndarray, length: int = 12) -> str:
    """Stable ID for a prediction array, canonicalized as little-endian float32."""

    value = np.ascontiguousarray(np.asarray(array, dtype="<f4"))
    return hashlib.sha256(value.tobytes()).hexdigest()[:length]


def grid_from_path(path: str | Path) -> Grid:
    with rasterio.open(path) as dataset:
        return Grid.from_dataset(dataset)


def assert_same_grid(
    left: str | Path | Grid,
    right: str | Path | Grid,
    *,
    left_name: str = "left raster",
    right_name: str = "right raster",
) -> None:
    """Raise a clear error unless shape, CRS, and affine transform are identical."""

    left_grid = grid_from_path(left) if not isinstance(left, Grid) else left
    right_grid = grid_from_path(right) if not isinstance(right, Grid) else right
    mismatches: list[str] = []
    if left_grid.shape != right_grid.shape:
        mismatches.append(f"shape {left_grid.shape} != {right_grid.shape}")
    if left_grid.crs_wkt != right_grid.crs_wkt:
        mismatches.append("CRS differs")
    if left_grid.transform != right_grid.transform:
        mismatches.append(
            f"transform {tuple(left_grid.transform)[:6]} != {tuple(right_grid.transform)[:6]}"
        )
    if mismatches:
        raise ValueError(f"{left_name} and {right_name} do not share a grid: " + "; ".join(mismatches))


def template_footprint(template_path: str | Path) -> tuple[np.ndarray, dict[str, Any], Grid]:
    """Read the organizer template footprint and a safe writing profile.

    The template's finite cells are the only inferred footprint.  Its prediction
    values are never used as a model feature or target.
    """

    with rasterio.open(template_path) as template:
        if template.count != 1:
            raise ValueError(f"Template must have one band, got {template.count}")
        template_values = template.read(1)
        footprint = np.isfinite(template_values)
        if not footprint.any():
            raise ValueError("Template has no finite cells; cannot infer a submission footprint")
        profile = template.profile.copy()
        grid = Grid.from_dataset(template)
    return footprint, profile, grid


def read_single_band(path: str | Path, *, name: str = "raster") -> np.ndarray:
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"{name} must have exactly one band, got {dataset.count}")
        return dataset.read(1)
