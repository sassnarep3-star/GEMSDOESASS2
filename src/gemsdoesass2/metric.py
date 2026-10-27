"""Distance-weighted Tversky Index used by the local holdout protocol.

This is an independently implemented local evaluator, not an organizer scoring
service.  It follows the metric parameters stated in the project brief:
``alpha=0.2``, ``beta=0.8``, and a 300 m triangular credit kernel.  The radius
is converted from metres using the template's (square) pixel size.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
KERNEL_RADIUS_M = 300.0
EPSILON = 1e-12


@dataclass(frozen=True)
class DTIComponents:
    true_positive_weight: float
    false_positive_weight: float
    false_negative_weight: float
    n_truth_pixels: int
    n_prediction_pixels: int
    prediction_mass: float
    dti: float
    coverage: float

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


def _validate_arrays(
    prediction: np.ndarray,
    truth: np.ndarray,
    valid_mask: np.ndarray | None,
    catalogue_mask: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    prediction = np.asarray(prediction, dtype=np.float64)
    raw_truth = np.asarray(truth)
    truth = raw_truth.astype(bool) if raw_truth.dtype == bool else (np.isfinite(raw_truth) & (raw_truth > 0))
    if prediction.ndim != 2 or prediction.shape != truth.shape:
        raise ValueError("prediction and truth must be same-shaped 2-D arrays")
    valid = np.ones(prediction.shape, dtype=bool) if valid_mask is None else np.asarray(valid_mask, dtype=bool)
    catalogue = (
        np.zeros(prediction.shape, dtype=bool)
        if catalogue_mask is None
        else np.asarray(catalogue_mask, dtype=bool)
    )
    if valid.shape != prediction.shape or catalogue.shape != prediction.shape:
        raise ValueError("valid_mask and catalogue_mask must match prediction shape")
    active = valid & ~catalogue
    active_values = prediction[active]
    if not np.isfinite(active_values).all() or np.any((active_values < 0.0) | (active_values > 1.0)):
        raise ValueError("predictions in the evaluated domain must be finite probabilities in [0,1]")
    # Values outside the active domain are deliberately neutral—not an implicit
    # source of positive credit or false-positive penalty.
    probability = np.where(active, prediction, 0.0)
    target = truth & active
    return probability, target, active, catalogue


def _soft_true_positive_credit(probability: np.ndarray, target: np.ndarray, radius_px: float) -> np.ndarray:
    """Return max triangular-kernel credit for each target pixel.

    The loops iterate over the small kernel footprint (at 100 m, 25 nonzero
    offsets) rather than over all target pixels, so soft and binary predictions
    use the same definition.
    """

    if not target.any():
        return np.empty(0, dtype=np.float64)
    pad = int(np.ceil(radius_px))
    padded = np.pad(probability, pad, mode="constant", constant_values=0.0)
    h, w = probability.shape
    best = np.zeros(probability.shape, dtype=np.float64)
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            distance = float(np.hypot(dy, dx))
            weight = max(1.0 - distance / radius_px, 0.0)
            if weight == 0.0:
                continue
            # At output y,x we need prediction y+dy,x+dx.  Padded slicing
            # protects every border without wraparound.
            shifted = padded[pad + dy : pad + dy + h, pad + dx : pad + dx + w]
            np.maximum(best, shifted * weight, out=best)
    return best[target]


def dti_components(
    prediction: np.ndarray,
    truth: np.ndarray,
    *,
    valid_mask: np.ndarray | None = None,
    catalogue_mask: np.ndarray | None = None,
    pixel_size_m: float = 100.0,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> DTIComponents:
    """Calculate the local exact distance-weighted Tversky components.

    ``catalogue_mask`` removes *visible* catalogue cells from evaluation.  In the
    hide-and-recover protocol, withheld positives must not appear in that mask.
    """

    if pixel_size_m <= 0 or alpha < 0 or beta < 0:
        raise ValueError("pixel_size_m must be positive and Tversky weights nonnegative")
    probability, target, active, _ = _validate_arrays(prediction, truth, valid_mask, catalogue_mask)
    radius_px = KERNEL_RADIUS_M / float(pixel_size_m)
    if radius_px <= 0:
        raise ValueError("kernel radius must be positive")

    n_truth = int(target.sum())
    n_prediction = int((probability > 0).sum())
    mass = float(probability.sum(dtype=np.float64))
    if n_truth == 0:
        false_positive = mass
        return DTIComponents(0.0, false_positive, 0.0, 0, n_prediction, mass, 0.0, 0.0)

    credit = _soft_true_positive_credit(probability, target, radius_px)
    true_positive = float(credit.sum(dtype=np.float64))
    false_negative = float(n_truth) - true_positive

    # A prediction receives no false-positive penalty at a true positive; the
    # penalty rises linearly to one at the specified radius and is restricted to
    # the active evaluation domain.
    distance_to_truth = distance_transform_edt(~target)
    near_truth_credit = np.maximum(1.0 - distance_to_truth / radius_px, 0.0)
    false_positive_weight_map = np.where(active, 1.0 - near_truth_credit, 0.0)
    false_positive = float((probability * false_positive_weight_map).sum(dtype=np.float64))
    denominator = true_positive + alpha * false_positive + beta * false_negative
    dti = float(true_positive / (denominator + EPSILON))
    return DTIComponents(
        true_positive,
        false_positive,
        false_negative,
        n_truth,
        n_prediction,
        mass,
        dti,
        float(true_positive / n_truth),
    )


def components_to_array(components: DTIComponents) -> np.ndarray:
    """Return TP, FP, FN for pooled calculation without averaging ratios."""

    return np.asarray(
        [
            components.true_positive_weight,
            components.false_positive_weight,
            components.false_negative_weight,
        ],
        dtype=np.float64,
    )


def pooled_dti(component_rows: np.ndarray, *, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Pool TP/FP/FN before calculating DTI (never average fold ratios)."""

    rows = np.asarray(component_rows, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != 3:
        raise ValueError("component_rows must have shape (n, 3) for TP, FP, FN")
    if len(rows) == 0:
        return 0.0
    true_positive, false_positive, false_negative = rows.sum(axis=0)
    return float(true_positive / (true_positive + alpha * false_positive + beta * false_negative + EPSILON))


def worked_example() -> dict[str, Any]:
    """Published arithmetic check for the formula used in documentation/tests."""

    true_positive, false_positive, false_negative = 3.0, 1.89, 2.0
    value = true_positive / (true_positive + ALPHA * false_positive + BETA * false_negative)
    return {
        "TP_w": true_positive,
        "FP_w": false_positive,
        "FN_w": false_negative,
        "alpha": ALPHA,
        "beta": BETA,
        "dti": value,
        "rounded_two_decimals": round(value, 2),
    }
