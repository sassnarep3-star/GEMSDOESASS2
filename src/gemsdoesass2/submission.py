"""Strict portal-safe GeoTIFF writer and validator.

The DrivenData form reported by the project owner rejects a prediction when any
value falls outside ``[0, 1]``.  Therefore the portal-safe writer uses finite zero
outside the template footprint instead of propagating the template's NaN nodata.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .io import Grid, assert_same_grid, sha256_file, template_footprint


class SubmissionValidationError(ValueError):
    """Raised when a prediction cannot safely be written as a submission."""


def _checked_prediction(prediction: np.ndarray, shape: tuple[int, int], footprint: np.ndarray) -> np.ndarray:
    prediction = np.asarray(prediction)
    if prediction.ndim != 2 or prediction.shape != shape:
        raise SubmissionValidationError(
            f"Prediction must be 2-D and match template shape {shape}; got {prediction.shape}"
        )
    values = prediction[footprint]
    if not np.isfinite(values).all():
        raise SubmissionValidationError("Prediction contains NaN or infinity inside the template footprint")
    if np.any((values < 0.0) | (values > 1.0)):
        raise SubmissionValidationError("Prediction values inside the template footprint must lie in [0, 1]")
    return prediction.astype(np.float32, copy=False)


def write_portal_safe_submission(
    prediction: np.ndarray,
    template_path: str | Path,
    output_path: str | Path,
) -> Path:
    """Write a one-band, finite float32 GeoTIFF on the exact template grid.

    This function intentionally does *not* clip or sanitize invalid inputs.  A
    scientific pipeline must make any change to predictions explicit before this
    final writer; otherwise a faulty model could be silently converted into a
    misleadingly valid-looking artifact.
    """

    output_path = Path(output_path)
    footprint, profile, _ = template_footprint(template_path)
    checked = _checked_prediction(prediction, footprint.shape, footprint)
    values = np.where(footprint, checked, np.float32(0.0)).astype(np.float32, copy=False)

    # Preserve spatial metadata, but deliberately clear NaN nodata to meet the
    # conservative whole-array [0,1] requirement reported by the portal.
    profile.update(
        driver="GTiff",
        height=values.shape[0],
        width=values.shape[1],
        count=1,
        dtype="float32",
        nodata=None,
        compress="lzw",
        interleave="band",
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **profile) as destination:
        destination.write(values, 1)
        destination.update_tags(AREA_OR_POINT="Area")
    return output_path


def validate_submission(path: str | Path, template_path: str | Path) -> dict[str, Any]:
    """Validate format only; this never authorizes a competition slot.

    The validator is intentionally stricter than a NaN-aware interpretation of a
    template.  It requires all pixels—not only the footprint—to be finite values
    within ``[0,1]`` so that the known portal error cannot recur.
    """

    path = Path(path)
    template_path = Path(template_path)
    checks: dict[str, dict[str, Any]] = {}

    def record(name: str, passed: bool, detail: str) -> None:
        checks[name] = {"pass": bool(passed), "detail": detail}

    template_foot, _, template_grid = template_footprint(template_path)
    try:
        with rasterio.open(path) as candidate:
            candidate_grid = Grid.from_dataset(candidate)
            count = candidate.count
            dtype = candidate.dtypes[0] if count else None
            array = candidate.read(1) if count == 1 else np.empty((0, 0), dtype=np.float32)
            driver = candidate.driver
            nodata = candidate.nodata
    except Exception as error:  # rasterio includes corrupted-TIFF errors here
        return {
            "file": path.name,
            "format_valid": False,
            "submission_authorized": False,
            "errors": [f"Could not open GeoTIFF: {error}"],
            "checks": {},
        }

    record("single_band", count == 1, f"band count={count}")
    record("gtiff_driver", driver == "GTiff", f"driver={driver}")
    record("float32", dtype == "float32", f"dtype={dtype}")
    record("shape_matches_template", candidate_grid.shape == template_grid.shape, str(candidate_grid.shape))
    record("crs_matches_template", candidate_grid.crs_wkt == template_grid.crs_wkt, "exact WKT comparison")
    record(
        "transform_matches_template",
        candidate_grid.transform == template_grid.transform,
        f"transform={tuple(candidate_grid.transform)[:6]}",
    )

    same_shape = candidate_grid.shape == template_grid.shape and count == 1
    all_finite = bool(np.isfinite(array).all()) if array.size else False
    in_range = bool(np.all((array >= 0.0) & (array <= 1.0))) if all_finite and array.size else False
    record("all_values_finite", all_finite, f"nonfinite={int((~np.isfinite(array)).sum()) if array.size else 'n/a'}")
    record(
        "all_values_in_range_0_1",
        in_range,
        (
            f"min={float(array.min()) if array.size and all_finite else 'n/a'}, "
            f"max={float(array.max()) if array.size and all_finite else 'n/a'}"
        ),
    )
    if same_shape:
        footprint_values = array[template_foot]
        record(
            "footprint_finite_in_range",
            bool(np.isfinite(footprint_values).all() and np.all((footprint_values >= 0) & (footprint_values <= 1))),
            f"footprint pixels={int(template_foot.sum())}",
        )
    else:
        record("footprint_finite_in_range", False, "not evaluated because shape or band count differs")
    record("portal_safe_zero_outside", nodata is None, f"nodata={nodata!r}; finite zeros are required outside")

    errors = [name for name, result in checks.items() if not result["pass"]]
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "format_valid": not errors,
        "portal_safe": not errors,
        "submission_authorized": False,
        "scope": "format-only validation; scientific, provenance, uniqueness, and weekly-slot gates are separate",
        "errors": errors,
        "checks": checks,
    }


def write_single_tif_zip(tif_path: str | Path, zip_path: str | Path | None = None) -> Path:
    """Create and verify a zip containing exactly the requested GeoTIFF."""

    tif_path = Path(tif_path)
    if tif_path.suffix.lower() not in {".tif", ".tiff"} or not tif_path.is_file():
        raise ValueError("A pre-existing .tif/.tiff is required")
    zip_path = Path(zip_path) if zip_path else tif_path.with_suffix(".zip")
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(tif_path, arcname=tif_path.name)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if names != [tif_path.name]:
            raise RuntimeError("ZIP must contain exactly one GeoTIFF with its original name")
        if archive.read(tif_path.name) != tif_path.read_bytes():
            raise RuntimeError("ZIP payload differs from its source GeoTIFF")
    return zip_path


def make_submission_note(hypothesis_id: str, summary: str, content_id: str, *, limit: int = 140) -> str:
    """Make a bounded, unambiguous submission note suitable for the portal field."""

    note = f"{hypothesis_id} | {summary} | id {content_id}"
    if len(note) > limit:
        note = note[:limit].rstrip()
    if len(note) > limit:
        raise AssertionError("note shortening failed")
    return note


def save_validation_report(report: dict[str, Any], output_path: str | Path) -> None:
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
