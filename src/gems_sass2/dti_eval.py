"""Exact distance-weighted Tversky evaluator for *emission policies*.

The official metric (DrivenData GEMS page/967) is

    TP_w = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
    FP_w = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
    DTI  = TP_w / (TP_w + alpha FP_w + beta FN_w + eps),  alpha=0.2, beta=0.8

with k(d) = max(1 - d/R, 0), R = 3 px = 300 m.

Because FN_w = |G| - TP_w, the metric is exactly

    DTI = TP_w / (0.2 TP_w + 0.2 FP_w + 0.8 |G|)

so for a *fixed* target set the score is maximised by trading prediction mass
against target coverage at an exchange rate of 0.2.  That identity is what
makes the emission sweep below meaningful: we can compute TP_w and FP_w for a
whole family of emission policies and read off the optimum directly, instead of
guessing a probability threshold.

Everything here is a HOLDOUT-DTI diagnostic.  It is never a leaderboard score.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt

R_PX = 3.0
ALPHA = 0.2
BETA = 0.8


def kernel(d: np.ndarray) -> np.ndarray:
    return np.clip(1.0 - np.asarray(d, np.float64) / R_PX, 0.0, 1.0)


def dti_terms(pred: np.ndarray, truth: np.ndarray) -> dict:
    """Exact TP_w, FP_w, FN_w, |G| and DTI for a whole-grid prediction."""
    p = np.asarray(pred, np.float64)
    p = np.where(np.isfinite(p), p, 0.0)
    p = np.clip(p, 0.0, 1.0)
    g = np.asarray(truth, bool)

    d_to_truth = distance_transform_edt(~g)
    k_truth = kernel(d_to_truth)

    fp = float((p * (1.0 - k_truth)).sum()) if p.any() else 0.0

    n_truth = int(g.sum())
    if n_truth == 0:
        return dict(T=0.0, F=fp, FN=0.0, G=0, DTI=0.0)
    if not p.any():
        return dict(T=0.0, F=0.0, FN=float(n_truth), G=n_truth, DTI=0.0)

    d_to_pred = distance_transform_edt(p <= 0.0)
    tp = float(kernel(d_to_pred[g]).sum())
    fn = n_truth - tp
    dti = tp / (ALPHA * tp + ALPHA * fp + BETA * fn) if tp > 0 else 0.0
    return dict(T=tp, F=fp, FN=fn, G=n_truth, DTI=float(dti))


def band(mask: np.ndarray, width: int) -> np.ndarray:
    """Binary dilation with a square structuring element of the given radius."""
    if width <= 0:
        return mask
    return binary_dilation(mask, iterations=width)


def emit_threshold(prob: np.ndarray, q: float, allowed: np.ndarray | None = None) -> np.ndarray:
    """Binary emission: keep the top `q` fraction of the allowed cells."""
    p = np.where(np.isfinite(prob), prob, -np.inf)
    if allowed is not None:
        p = np.where(allowed, p, -np.inf)
    vals = p[np.isfinite(p)]
    if vals.size == 0:
        return np.zeros_like(prob, bool)
    thr = np.quantile(vals, 1.0 - q)
    return np.isfinite(p) & (p >= thr) & (p > 0)


def sweep(prob: np.ndarray, targets: dict[str, np.ndarray], *,
          quantiles: tuple[float, ...] = (0.002, 0.004, 0.006, 0.008, 0.012, 0.018,
                                          0.025, 0.035, 0.05, 0.07),
          widths: tuple[int, ...] = (0, 1, 2),
          allowed: np.ndarray | None = None) -> list[dict]:
    """Evaluate every (quantile, band width) policy against every target."""
    rows = []
    cache: dict[tuple[float, int], np.ndarray] = {}
    for q in quantiles:
        core = emit_threshold(prob, q, allowed)
        for w in widths:
            mask = band(core, w)
            if allowed is not None:
                mask &= allowed
            pred = mask.astype(np.float32)
            cache[(q, w)] = pred
            rec = {"q": q, "width": w, "n_cells": int(mask.sum())}
            for name, tgt in targets.items():
                rec[name] = dti_terms(pred, tgt)
            rows.append(rec)
    return rows
