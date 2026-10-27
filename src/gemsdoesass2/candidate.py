"""The CDCC geological hypothesis: cross-domain contact concordance.

CDCC is deliberately a static, label-free surface.  It seeks co-located sharp
changes in upward-continued magnetic intensity and U/Th radiometric ratio.  Such
coincidence can mark a concealed structural boundary that juxtaposes alteration
or lithologic domains, but it can also arise at a non-fault lithologic contact,
an intrusive margin, a survey seam, or a processing artifact.  Those confounds
are recorded in the run card rather than hidden by a model label.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

from .io import assert_same_grid, sha256_file, template_footprint

HYPOTHESIS_ID = "CDCC-01"
HYPOTHESIS_NAME = "GeoDAWN cross-domain contact concordance"
MAGNETIC_BAND = 4  # TMI upward-continued to 150 m in the pinned mirror manifest
RADIOMETRIC_BAND = 3  # U/Th in the pinned mirror manifest
SHORT_SCALE_PX = 0.8
LOW_QUANTILE = 0.05
HIGH_QUANTILE = 0.995


@dataclass(frozen=True)
class CDCCInputs:
    template: Path
    extensions: Path
    radiometric: Path


def _normalized_edge_energy(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Compute a robust local gradient magnitude without treating nodata edges as geology."""

    if not valid.any():
        raise ValueError("No overlapping valid pixels for CDCC feature construction")
    values = np.asarray(values, dtype=np.float32)
    fill = float(np.median(values[valid]))
    filled = np.where(valid, values, fill)
    smoothed = gaussian_filter(filled, sigma=SHORT_SCALE_PX, mode="nearest")
    gradient_y, gradient_x = np.gradient(smoothed)
    energy = np.hypot(gradient_y, gradient_x).astype(np.float32)
    energy[~valid] = 0.0
    low, high = np.quantile(energy[valid], [LOW_QUANTILE, HIGH_QUANTILE])
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError("Feature edge distribution has no usable dynamic range")
    normalized = np.clip((energy - low) / (high - low), 0.0, 1.0).astype(np.float32)
    normalized[~valid] = 0.0
    return normalized


def compute_cdcc_surface(
    magnetic_up150: np.ndarray,
    radiometric_u_th: np.ndarray,
    footprint: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    """Construct the preregistered static CDCC surface.

    The geometric mean requires support from both sensors.  No catalogue, label,
    registry raster, or historical submission enters this calculation.
    """

    magnetic_up150 = np.asarray(magnetic_up150, dtype=np.float32)
    radiometric_u_th = np.asarray(radiometric_u_th, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    if magnetic_up150.shape != footprint.shape or radiometric_u_th.shape != footprint.shape:
        raise ValueError("CDCC inputs and footprint must have identical dimensions")
    valid = (
        footprint
        & np.isfinite(magnetic_up150)
        & np.isfinite(radiometric_u_th)
        & (magnetic_up150 > 0)
        & (radiometric_u_th > 0)
    )
    magnetic_edge = _normalized_edge_energy(magnetic_up150, valid)
    radiometric_edge = _normalized_edge_energy(radiometric_u_th, valid)
    consensus = np.sqrt(magnetic_edge * radiometric_edge).astype(np.float32, copy=False)
    consensus[~valid] = 0.0
    features = {
        "magnetic_up150_edge": magnetic_edge,
        "radiometric_u_th_edge": radiometric_edge,
        "cdcc_consensus": consensus,
    }
    return consensus, features, valid


def load_cdcc_inputs(inputs: CDCCInputs) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, dict[str, Any]]:
    """Load exact-grid GeoDAWN bands and return CDCC surface plus provenance.

    The band semantics are verified against the pinned sidecar manifests by the
    caller's data-provenance workflow.  This reader still checks every raster's
    grid locally before a scientific result is created.
    """

    footprint, _, _ = template_footprint(inputs.template)
    assert_same_grid(inputs.template, inputs.extensions, left_name="template", right_name="GeoDAWN extensions")
    assert_same_grid(inputs.template, inputs.radiometric, left_name="template", right_name="GeoDAWN radiometric")
    with rasterio.open(inputs.extensions) as extensions:
        if extensions.count < MAGNETIC_BAND:
            raise ValueError(f"Extensions raster has {extensions.count} bands; band {MAGNETIC_BAND} is required")
        magnetic = extensions.read(MAGNETIC_BAND).astype(np.float32)
    with rasterio.open(inputs.radiometric) as radiometric:
        if radiometric.count < RADIOMETRIC_BAND:
            raise ValueError(f"Radiometric raster has {radiometric.count} bands; band {RADIOMETRIC_BAND} is required")
        u_th = radiometric.read(RADIOMETRIC_BAND).astype(np.float32)
    surface, features, support = compute_cdcc_surface(magnetic, u_th, footprint)
    provenance = {
        "template": {"path": str(inputs.template), "sha256": sha256_file(inputs.template)},
        "extensions": {"path": str(inputs.extensions), "sha256": sha256_file(inputs.extensions), "band": MAGNETIC_BAND},
        "radiometric": {"path": str(inputs.radiometric), "sha256": sha256_file(inputs.radiometric), "band": RADIOMETRIC_BAND},
        "parameters": {
            "short_scale_px": SHORT_SCALE_PX,
            "normalization_quantiles": [LOW_QUANTILE, HIGH_QUANTILE],
            "fusion": "geometric_mean",
        },
        "supported_pixels": int(support.sum()),
    }
    return surface, features, support, provenance
