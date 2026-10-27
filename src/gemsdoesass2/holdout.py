"""Leakage-resistant segment hide-and-recover evaluation.

The public catalogue is treated as a proxy target for methodological screening,
not as organizer hidden truth.  Each connected catalogue segment is assigned to
one spatial block as a whole; a buffered neighborhood is removed from the
visible catalogue before any catalogue-based operation occurs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Sequence

import numpy as np
from scipy.ndimage import binary_dilation, label as connected_components, maximum_filter
from scipy.stats import rankdata

from .metric import DTIComponents, components_to_array, dti_components, pooled_dti

EVALUATOR_VERSION = "gemsdoesass2-segment-pooled-v1"
DEFAULT_BUFFER_PX = 3
DEFAULT_BOOTSTRAPS = 2_000


@dataclass(frozen=True)
class Fold:
    index: int
    name: str
    hidden_component_ids: np.ndarray
    hidden: np.ndarray
    visible_catalogue: np.ndarray


@dataclass(frozen=True)
class SegmentHoldout:
    footprint: np.ndarray
    labels: np.ndarray
    components: np.ndarray
    folds: tuple[Fold, ...]
    buffer_px: int

    @property
    def n_withheld_positive_pixels(self) -> int:
        return int(sum(int(fold.hidden.sum()) for fold in self.folds))

    @property
    def n_segments(self) -> int:
        return int(self.components.max())


def _fold_assignment_from_centroids(
    components: np.ndarray,
    footprint: np.ndarray,
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Assign every 8-connected segment to a quadrant by its centroid.

    A whole segment never straddles train/holdout even when its pixels cross a
    quadrant boundary.  Four broad blocks intentionally make the local
    bootstrap conservative relative to random pixel splits.
    """

    n_components = int(components.max())
    if n_components == 0:
        raise ValueError("At least one labelled segment is required")
    yy, xx = np.indices(components.shape)
    counts = np.bincount(components.ravel(), minlength=n_components + 1)[1:]
    sums_y = np.bincount(components.ravel(), weights=yy.ravel(), minlength=n_components + 1)[1:]
    sums_x = np.bincount(components.ravel(), weights=xx.ravel(), minlength=n_components + 1)[1:]
    centroids_y = sums_y / counts
    centroids_x = sums_x / counts
    footprint_y, footprint_x = np.nonzero(footprint)
    y_mid = float(np.median(footprint_y))
    x_mid = float(np.median(footprint_x))
    assignment = ((centroids_y >= y_mid).astype(np.int8) * 2 + (centroids_x >= x_mid).astype(np.int8))
    names = ("NW", "NE", "SW", "SE")
    return assignment, names


def make_segment_holdout(
    footprint: np.ndarray,
    labels: np.ndarray,
    *,
    buffer_px: int = DEFAULT_BUFFER_PX,
) -> SegmentHoldout:
    """Create four spatial, whole-segment hide-and-recover folds.

    ``labels`` should be the publicly available known-fault catalogue.  It is
    never used in a feature surface by this function.  The returned folds expose
    only their ``visible_catalogue`` to a caller that needs a catalogue-based
    feature or output mask.
    """

    footprint = np.asarray(footprint, dtype=bool)
    raw_labels = np.asarray(labels)
    # Avoid NumPy's surprising bool(NaN) == True behavior when a caller passes
    # a raster directly instead of the preferred explicit ``raster > 0`` mask.
    labels = raw_labels.astype(bool) if raw_labels.dtype == bool else (np.isfinite(raw_labels) & (raw_labels > 0))
    labels = labels & footprint
    if footprint.ndim != 2 or labels.shape != footprint.shape or not footprint.any():
        raise ValueError("A nonempty aligned 2-D footprint and labels grid are required")
    if buffer_px < 0:
        raise ValueError("buffer_px must be nonnegative")
    components, n_components = connected_components(labels, structure=np.ones((3, 3), dtype=np.uint8))
    if n_components == 0:
        raise ValueError("No labelled positive pixels available for holdout")
    assignment, names = _fold_assignment_from_centroids(components, footprint)
    folds: list[Fold] = []
    for fold_index, fold_name in enumerate(names):
        ids = np.flatnonzero(assignment == fold_index).astype(np.int32) + 1
        if len(ids) == 0:
            raise ValueError(f"Spatial fold {fold_name} contains no complete segments")
        hidden = np.isin(components, ids)
        if buffer_px:
            structure = np.ones((2 * buffer_px + 1, 2 * buffer_px + 1), dtype=bool)
            hidden_buffer = binary_dilation(hidden, structure=structure)
        else:
            hidden_buffer = hidden
        # The buffered zone prevents an adjacent labelled segment from becoming
        # a visible source feature for a withheld fault.  Only the actual visible
        # catalogue pixels are later masked pixel-exactly.
        visible = labels & ~hidden_buffer
        folds.append(Fold(fold_index, fold_name, ids, hidden, visible))
    result = SegmentHoldout(footprint, labels, components, tuple(folds), buffer_px)
    reconstructed = np.zeros_like(labels)
    for fold in result.folds:
        if (fold.hidden & reconstructed).any():
            raise RuntimeError("A catalogue segment was split between holdout folds")
        reconstructed |= fold.hidden
    if not np.array_equal(reconstructed, labels):
        raise RuntimeError("Whole-segment holdout does not cover every labelled positive exactly once")
    return result


def select_top_local_maxima(
    surface: np.ndarray,
    eligible: np.ndarray,
    *,
    budget: int,
    nms_size: int = 3,
) -> np.ndarray:
    """Deterministically select positive local maxima without padding with zeros.

    ``eligible`` may contain a fold's visible-catalogue exclusion.  This is the
    only place output placement can depend on the catalogue; the input surface is
    supplied separately and should be independent of hidden labels.
    """

    surface = np.asarray(surface, dtype=np.float64)
    eligible = np.asarray(eligible, dtype=bool)
    if surface.ndim != 2 or surface.shape != eligible.shape:
        raise ValueError("surface and eligible mask must be aligned 2-D arrays")
    if budget <= 0 or nms_size < 1:
        raise ValueError("budget and nms_size must be positive")
    masked_surface = np.where(eligible & np.isfinite(surface), surface, 0.0)
    maxima = maximum_filter(masked_surface, size=nms_size, mode="nearest")
    candidates = eligible & (masked_surface > 0.0) & (masked_surface >= maxima)
    indices = np.flatnonzero(candidates.ravel())
    if len(indices) < budget:
        raise ValueError(
            f"Only {len(indices)} positive local maxima exist, fewer than requested budget {budget}; do not pad"
        )
    # Stable row-major tie-breaker avoids random placements and makes every run
    # hash-reproducible.
    order = np.lexsort((indices, -masked_surface.ravel()[indices]))
    chosen = indices[order[:budget]]
    result = np.zeros(surface.shape, dtype=bool)
    result.ravel()[chosen] = True
    return result


def _bootstrap_ci(component_rows: np.ndarray, *, seed: int, n_bootstraps: int) -> tuple[float, float]:
    rows = np.asarray(component_rows, dtype=np.float64)
    if rows.ndim != 2 or rows.shape[1] != 3 or len(rows) < 2:
        raise ValueError("At least two [TP, FP, FN] spatial-block rows are required")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(rows), size=(n_bootstraps, len(rows)))
    sampled = rows[draws].sum(axis=1)
    values = sampled[:, 0] / (sampled[:, 0] + 0.2 * sampled[:, 1] + 0.8 * sampled[:, 2] + 1e-12)
    lo, hi = np.quantile(values, [0.025, 0.975])
    return float(lo), float(hi)


def _paired_bootstrap_delta(
    candidate_rows: np.ndarray,
    baseline_rows: np.ndarray,
    *,
    seed: int,
    n_bootstraps: int,
) -> dict[str, float]:
    candidate_rows = np.asarray(candidate_rows, dtype=np.float64)
    baseline_rows = np.asarray(baseline_rows, dtype=np.float64)
    if candidate_rows.shape != baseline_rows.shape or candidate_rows.ndim != 2 or candidate_rows.shape[1] != 3:
        raise ValueError("Paired bootstrap requires equal (blocks, TP/FP/FN) arrays")
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, len(candidate_rows), size=(n_bootstraps, len(candidate_rows)))

    def score(rows: np.ndarray) -> np.ndarray:
        totals = rows.sum(axis=1)
        return totals[:, 0] / (totals[:, 0] + 0.2 * totals[:, 1] + 0.8 * totals[:, 2] + 1e-12)

    delta_samples = score(candidate_rows[draws]) - score(baseline_rows[draws])
    point = pooled_dti(candidate_rows) - pooled_dti(baseline_rows)
    return {
        "point_delta": float(point),
        "ci95_low": float(np.quantile(delta_samples, 0.025)),
        "ci95_high": float(np.quantile(delta_samples, 0.975)),
        "probability_candidate_greater": float(np.mean(delta_samples > 0.0)),
    }


def evaluate_surface(
    holdout: SegmentHoldout,
    surface: np.ndarray,
    *,
    pixel_size_m: float,
    budget: int,
    nms_size: int = 3,
    bootstrap_seed: int = 20261027,
    n_bootstraps: int = DEFAULT_BOOTSTRAPS,
) -> dict[str, object]:
    """Evaluate a label-independent surface under the whole-segment protocol."""

    surface = np.asarray(surface, dtype=np.float64)
    if surface.shape != holdout.footprint.shape:
        raise ValueError("surface and holdout grid differ")
    block_rows: list[np.ndarray] = []
    fold_reports: list[dict[str, object]] = []
    for fold in holdout.folds:
        eligible = holdout.footprint & ~fold.visible_catalogue
        emitted = select_top_local_maxima(surface, eligible, budget=budget, nms_size=nms_size)
        components = dti_components(
            emitted.astype(np.float32),
            fold.hidden,
            valid_mask=holdout.footprint,
            catalogue_mask=fold.visible_catalogue,
            pixel_size_m=pixel_size_m,
        )
        block_rows.append(components_to_array(components))
        fold_reports.append(
            {
                "fold": fold.name,
                "withheld_segment_count": int(len(fold.hidden_component_ids)),
                "withheld_positive_pixels": int(fold.hidden.sum()),
                "visible_catalogue_pixels": int(fold.visible_catalogue.sum()),
                "emitted_dots": int(emitted.sum()),
                "dti": components.to_dict(),
            }
        )
    rows = np.asarray(block_rows, dtype=np.float64)
    ci_low, ci_high = _bootstrap_ci(rows, seed=bootstrap_seed, n_bootstraps=n_bootstraps)
    return {
        "label": "HOLDOUT-DTI",
        "evaluator_version": EVALUATOR_VERSION,
        "kernel": {"alpha": 0.2, "beta": 0.8, "radius_m": 300.0, "shape": "triangular"},
        "n_withheld_positive_pixels": holdout.n_withheld_positive_pixels,
        "n_whole_segments": holdout.n_segments,
        "n_spatial_blocks": len(holdout.folds),
        "buffer_px": holdout.buffer_px,
        "budget_dots_per_fold": budget,
        "nms_size_px": nms_size,
        "pooled_dti": pooled_dti(rows),
        "ci95": {"low": ci_low, "high": ci_high, "method": "spatial-block bootstrap", "draws": n_bootstraps},
        "folds": fold_reports,
        # Kept for paired comparisons, deliberately not serialized by JSON callers
        # until transformed to a list.
        "_component_rows": rows,
    }


def paired_holdout_delta(
    candidate: Mapping[str, object],
    baseline: Mapping[str, object],
    *,
    seed: int = 20261027,
    n_bootstraps: int = DEFAULT_BOOTSTRAPS,
) -> dict[str, float]:
    """Compare two arms evaluated on the exact same spatial blocks."""

    candidate_rows = np.asarray(candidate["_component_rows"], dtype=np.float64)
    baseline_rows = np.asarray(baseline["_component_rows"], dtype=np.float64)
    return _paired_bootstrap_delta(candidate_rows, baseline_rows, seed=seed, n_bootstraps=n_bootstraps)


def roc_auc_balanced(
    surface: np.ndarray,
    positives: np.ndarray,
    domain: np.ndarray,
    *,
    seed: int,
) -> float:
    """A deterministic balanced ROC-AUC for leakage-canary screening.

    AUC above 0.90 is treated as leakage until proven otherwise.  We sample
    equally many negatives to make a rare positive catalogue numerically stable;
    this is a *canary*, not a performance score.
    """

    surface = np.asarray(surface, dtype=np.float64)
    positives = np.asarray(positives, dtype=bool)
    domain = np.asarray(domain, dtype=bool)
    if surface.shape != positives.shape or surface.shape != domain.shape:
        raise ValueError("AUC surface, positives, and domain must share shape")
    positive_indices = np.flatnonzero((positives & domain).ravel())
    negative_indices = np.flatnonzero((~positives & domain & np.isfinite(surface)).ravel())
    if len(positive_indices) == 0 or len(negative_indices) == 0:
        raise ValueError("AUC requires both positive and negative values")
    rng = np.random.default_rng(seed)
    negative_indices = rng.choice(negative_indices, size=min(len(positive_indices), len(negative_indices)), replace=False)
    values = np.concatenate((surface.ravel()[positive_indices], surface.ravel()[negative_indices]))
    if not np.isfinite(values).all():
        raise ValueError("AUC surface contains nonfinite values in the sampled domain")
    n_positive = len(positive_indices)
    ranks = rankdata(values, method="average")
    return float((ranks[:n_positive].sum() - n_positive * (n_positive + 1) / 2.0) / (n_positive * len(negative_indices)))


def leakage_canary(
    holdout: SegmentHoldout,
    features: Mapping[str, np.ndarray],
    *,
    threshold: float = 0.90,
    seed: int = 20261027,
) -> dict[str, object]:
    """Screen each raw/transformed feature independently before model trust."""

    if not features:
        raise ValueError("At least one feature is required for leakage screening")
    report: dict[str, object] = {"threshold_auc": threshold, "features": {}}
    overall_pass = True
    for name, feature in features.items():
        feature = np.asarray(feature, dtype=np.float64)
        if feature.shape != holdout.footprint.shape:
            raise ValueError(f"Feature {name!r} does not match holdout grid")
        per_fold: dict[str, float] = {}
        for fold in holdout.folds:
            # Feature values must not be built from the hidden truth.  This AUC
            # only diagnoses suspicious prediction power after construction.
            auc = roc_auc_balanced(feature, fold.hidden, holdout.footprint, seed=seed + fold.index)
            per_fold[fold.name] = auc
        max_auc = max(per_fold.values())
        passed = max_auc <= threshold
        overall_pass = overall_pass and passed
        report["features"][name] = {"fold_auc": per_fold, "max_auc": max_auc, "pass": passed}
    report["pass"] = overall_pass
    return report


def strip_internal_arrays(report: Mapping[str, object]) -> dict[str, object]:
    """Return a JSON-safe copy without private component rows."""

    output: dict[str, object] = {}
    for key, value in report.items():
        if key.startswith("_"):
            continue
        if isinstance(value, np.ndarray):
            output[key] = value.tolist()
        elif isinstance(value, dict):
            output[key] = strip_internal_arrays(value)
        elif isinstance(value, list):
            output[key] = [strip_internal_arrays(v) if isinstance(v, dict) else v for v in value]
        elif isinstance(value, np.generic):
            output[key] = value.item()
        else:
            output[key] = value
    return output
