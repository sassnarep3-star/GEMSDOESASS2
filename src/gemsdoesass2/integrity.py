"""Input-provenance and mirror-integrity checks.

A GeoTIFF with a valid CRS is not automatically trusted.  In particular, a
public peer mirror may accidentally expose a sample raster that is pixel-identical
to a label raster.  That is an integrity anomaly, not a source of predictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio

from .io import assert_same_grid, sha256_file, template_footprint


def inspect_template_label_relationship(template_path: str | Path, labels_path: str | Path) -> dict[str, Any]:
    """Detect potentially unsafe equality between a template and a label raster."""

    template_path = Path(template_path)
    labels_path = Path(labels_path)
    assert_same_grid(template_path, labels_path, left_name="template", right_name="labels")
    footprint, _, _ = template_footprint(template_path)
    with rasterio.open(template_path) as template, rasterio.open(labels_path) as labels:
        if labels.count != 1:
            raise ValueError(f"labels must have exactly one band, got {labels.count}")
        template_values = template.read(1)
        label_values = labels.read(1)
    binary_labels = label_values > 0
    # Test both finite footprint identity and the actual binary pattern.  This
    # allows normal all-zero templates but flags a template that reproduces all
    # public known-fault pixels.
    finite_matches_nonnegative_labels = bool(np.array_equal(footprint, label_values >= 0))
    values_match_binary_labels = bool(
        np.array_equal(template_values[footprint].astype(np.float32), binary_labels[footprint].astype(np.float32))
    )
    exact_public_label_pattern = finite_matches_nonnegative_labels and values_match_binary_labels
    return {
        "template_sha256": sha256_file(template_path),
        "labels_sha256": sha256_file(labels_path),
        "template_finite_pixels": int(footprint.sum()),
        "label_positive_pixels": int(binary_labels.sum()),
        "template_ones_inside_footprint": int((template_values[footprint] == 1).sum()),
        "finite_footprint_matches_nonnegative_label_extent": finite_matches_nonnegative_labels,
        "template_values_match_binary_labels_inside_footprint": values_match_binary_labels,
        "exact_public_label_pattern_detected": exact_public_label_pattern,
        "promotion_gate_pass": not exact_public_label_pattern,
        "policy": (
            "A detected template/label identity blocks promotion. Template values are used only to define the grid/footprint; "
            "they are never used as a target or feature."
        ),
    }


def local_input_summary(paths: dict[str, str | Path]) -> dict[str, Any]:
    """Hash local files and record existence without pretending they are official."""

    summary: dict[str, Any] = {}
    for name, raw_path in paths.items():
        path = Path(raw_path)
        summary[name] = {
            "path": str(path),
            "exists": path.is_file(),
            "sha256": sha256_file(path) if path.is_file() else None,
        }
    return summary
