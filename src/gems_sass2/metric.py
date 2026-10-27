"""Exact competition Distance-Weighted Tversky Index (DW-Tversky / DTI).

Verified against DrivenData Competition #306 Problem Description (`page/967`):
  - Euclidean distance tolerance: R = 300 m = 3.0 pixels at 100 m resolution
  - Triangular linear decay kernel: k(d) = max(1 - d / 3.0, 0.0)
  - Asymmetry weights: alpha = 0.2 (false positives), beta = 0.8 (false negatives)
  - Scored domain: strictly valid footprint excluding known catalogue pixels (`valid & ~known`)
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA: float = 0.2
BETA: float = 0.8
RADIUS_PX: float = 3.0
EPS: float = 1e-12


def kernel(distance_px: np.ndarray | float, radius_px: float = RADIUS_PX) -> np.ndarray:
    d = np.asarray(distance_px, dtype=np.float32)
    return np.maximum(np.float32(1.0) - d / np.float32(radius_px), np.float32(0.0))


def dti_from_totals(
    tp_w: float,
    fp_w: float,
    fn_w: float,
    alpha: float = ALPHA,
    beta: float = BETA,
    eps: float = EPS,
) -> float:
    return float(tp_w / (tp_w + alpha * fp_w + beta * fn_w + eps))


def binary_dti_components(
    pred: np.ndarray,
    truth: np.ndarray,
    eval_mask: np.ndarray,
    radius_px: float = RADIUS_PX,
) -> tuple[float, float, float]:
    """Return exact (TP_w, FP_w, FN_w) for binary prediction and binary truth on eval_mask."""
    g = np.asarray(truth, dtype=bool) & eval_mask
    p = (np.asarray(pred) > 0) & eval_mask
    n_g = int(g.sum())
    n_p = int(p.sum())
    if n_g == 0:
        return 0.0, float(n_p), 0.0
    if n_p == 0:
        return 0.0, 0.0, float(n_g)

    d_to_p = distance_transform_edt(~p)
    tp_credits = kernel(d_to_p[g], radius_px=radius_px).astype(np.float64)
    tp_w = float(tp_credits.sum())
    fn_w = float(n_g) - tp_w

    d_to_g = distance_transform_edt(~g)
    fp_credits = (1.0 - kernel(d_to_g[p], radius_px=radius_px)).astype(np.float64)
    fp_w = float(fp_credits.sum())
    return tp_w, fp_w, fn_w


def dti_binary_fast(
    pred: np.ndarray,
    truth: np.ndarray,
    valid_mask: np.ndarray,
    known_mask: np.ndarray | None = None,
    alpha: float = ALPHA,
    beta: float = BETA,
    radius_px: float = RADIUS_PX,
) -> dict:
    eval_mask = np.asarray(valid_mask, dtype=bool)
    if known_mask is not None:
        eval_mask = eval_mask & ~np.asarray(known_mask, dtype=bool)
    tp_w, fp_w, fn_w = binary_dti_components(pred, truth, eval_mask, radius_px=radius_px)
    score = dti_from_totals(tp_w, fp_w, fn_w, alpha=alpha, beta=beta)
    return {
        "dti": score,
        "tp_w": tp_w,
        "fp_w": fp_w,
        "fn_w": fn_w,
        "n_truth": int((np.asarray(truth, dtype=bool) & eval_mask).sum()),
        "n_pred": int(((np.asarray(pred) > 0) & eval_mask).sum()),
    }
