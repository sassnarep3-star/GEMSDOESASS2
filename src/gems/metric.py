"""Pooled Distance-weighted Tversky Index (DTI).

See ``dti_probabilistic`` for the official continuous-probability form; ``dti_binary``
is its binary special case used for dot-set diagnostics.

Competition metric reconstruction (alpha=0.2, beta=0.8, 300 m triangular
kernel = 3 px at 100 m/px).  Identity (verified against GEMSDOE32
src/gems32/metric.py and the audit JSON of the 0.2778 champion):

    DTI = T / (T + 0.2*FP + 0.8*FN)

with, for a binary dot set P and truth set G (after masking known faults):
    T  = sum_{g in G} K(d(g, nearest p in P))      (weighted true positives)
    M  = sum_{p in P} K(d(p, nearest g in G))      (matched prediction mass)
    FP = |P| - M
    FN = |G| - T
    K(u) = max(0, 1 - u/3),  u in pixels (Euclidean), 3 px = 300 m.

All numbers produced with this module are HOLDOUT-DTI diagnostics, never
leaderboard scores.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

KERNEL_RADIUS_PX = 3.0  # 300 m at 100 m/px
ALPHA = 0.2
BETA = 0.8


def tri_kernel(dist_px: np.ndarray) -> np.ndarray:
    return np.clip(1.0 - dist_px / KERNEL_RADIUS_PX, 0.0, 1.0)


def dti_binary(pred_mask: np.ndarray, truth_mask: np.ndarray,
               score_mask: np.ndarray | None = None) -> dict:
    """Pooled DTI for binary dot predictions vs binary truth.

    score_mask: pixels eligible for scoring (True = scored).  Pixels outside
    are removed from both pred and truth before distances are computed
    (pixel-exact masking of visible/known faults).
    """
    pred = pred_mask.astype(bool).copy()
    truth = truth_mask.astype(bool).copy()
    if score_mask is not None:
        pred &= score_mask
        truth &= score_mask

    n_pred = int(pred.sum())
    n_truth = int(truth.sum())
    if n_truth == 0:
        return dict(dti=0.0, T=0.0, FP=float(n_pred), FN=0.0,
                    n_pred=n_pred, n_truth=0)
    if n_pred == 0:
        return dict(dti=0.0, T=0.0, FP=0.0, FN=float(n_truth),
                    n_pred=0, n_truth=n_truth)

    d_to_pred = distance_transform_edt(~pred)
    d_to_truth = distance_transform_edt(~truth)
    T = float(tri_kernel(d_to_pred[truth]).sum())
    M = float(tri_kernel(d_to_truth[pred]).sum())
    FP = n_pred - M
    FN = n_truth - T
    dti = T / (T + ALPHA * FP + BETA * FN) if T > 0 else 0.0
    return dict(dti=float(dti), T=T, FP=float(FP), FN=float(FN),
                n_pred=n_pred, n_truth=n_truth)


def dti_probabilistic(pred_prob: np.ndarray, truth_mask: np.ndarray,
                      score_mask: np.ndarray | None = None) -> dict:
    """Distance-weighted Tversky index for continuous probabilities p(x) in [0, 1].

    Implements the official definition on the DrivenData problem page (page/967,
    "Performance metric"), for alpha=0.2, beta=0.8 and R=3 px (300 m):

        TP_w = sum_{g in G} max_{x: d(x,g)<=R} p(x) k(d(x,g))
        FP_w = sum_{x: p(x)>0} p(x) [1 - max_{g in G} k(d(x,g))]
        FN_w = sum_{g in G} [1 - max_{x: d(x,g)<=R} p(x) k(d(x,g))]
        DTI  = TP_w / (TP_w + alpha*FP_w + beta*FN_w)

    with k(d) = max(1 - d/R, 0). The official epsilon is not published; it is
    omitted here (a zero denominator returns 0.0).

    Binary masks are a special case: for p in {0, 1} this equals ``dti_binary``.
    Outside ``score_mask`` the prediction is ignored and the truth is removed,
    matching the pixel-exact masking used elsewhere in this module. Non-finite
    values inside the scored area raise ValueError (the portal requires [0, 1]).
    """
    p = np.asarray(pred_prob, dtype=np.float64)
    truth = np.asarray(truth_mask).astype(bool).copy()
    if p.shape != truth.shape:
        raise ValueError("prediction and truth must share a shape")
    if score_mask is not None:
        scored = np.asarray(score_mask).astype(bool)
        truth &= scored
        p = np.where(scored, p, 0.0)
    if not np.all(np.isfinite(p[score_mask.astype(bool)] if score_mask is not None else p)):
        raise ValueError("non-finite prediction inside the scored area")
    if p.min(initial=0.0) < 0.0 or p.max(initial=0.0) > 1.0:
        raise ValueError("predicted probabilities must lie in [0, 1]")

    R = int(KERNEL_RADIUS_PX)
    rows, cols = np.nonzero(truth)
    n_truth = int(rows.size)
    sum_p = float(p.sum())

    # TP_w: per truth pixel, the best kernel-weighted probability within R.
    best = np.zeros(n_truth)
    H, W = p.shape
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            dist = float(np.hypot(dy, dx))
            if dist > KERNEL_RADIUS_PX:
                continue
            r2, c2 = rows + dy, cols + dx
            inside = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
            vals = np.zeros(n_truth)
            vals[inside] = p[r2[inside], c2[inside]] * float(tri_kernel(np.array([dist]))[0])
            np.maximum(best, vals, out=best)
    TP = float(best.sum())
    FN = float(n_truth - TP)

    # FP_w: each predicted mass is penalised by its distance to the nearest truth.
    if n_truth:
        k_nearest = tri_kernel(distance_transform_edt(~truth))
    else:
        k_nearest = np.zeros_like(p)
    FP = float(np.sum(p * (1.0 - k_nearest)))  # p == 0 contributes nothing by construction

    denom = TP + ALPHA * FP + BETA * FN
    dti = TP / denom if denom > 0 else 0.0
    return dict(dti=float(dti), TP=TP, FP=FP, FN=FN, n_truth=n_truth, sum_p=sum_p)


def per_component_terms(pred_mask: np.ndarray, truth_mask: np.ndarray,
                        truth_labels: np.ndarray, n_components: int) -> dict:
    """Decompose T, M, |G| per withheld truth component for cluster bootstrap.

    Each truth pixel contributes its kernel credit to its own component.
    Each predicted dot's matched mass M is attributed to the component of its
    nearest truth pixel.  Dots farther than 3 px from all truth are pure FP.
    """
    pred = pred_mask.astype(bool)
    truth = truth_mask.astype(bool)
    d_to_pred = distance_transform_edt(~pred)
    d_to_truth, idx = distance_transform_edt(~truth, return_indices=True)

    T_c = np.zeros(n_components + 1)
    G_c = np.zeros(n_components + 1)
    k_truth = tri_kernel(d_to_pred[truth])
    lab_truth = truth_labels[truth]
    np.add.at(T_c, lab_truth, k_truth)
    np.add.at(G_c, lab_truth, 1.0)

    M_c = np.zeros(n_components + 1)
    pr, pc = np.where(pred)
    kvals = tri_kernel(d_to_truth[pr, pc])
    near_lab = truth_labels[idx[0][pr, pc], idx[1][pr, pc]]
    np.add.at(M_c, near_lab, kvals)
    return dict(T_c=T_c, G_c=G_c, M_c=M_c, n_pred=int(pred.sum()))


def bootstrap_dti(terms: dict, component_ids: np.ndarray, n_boot: int = 500,
                  seed: int = 20261027) -> dict:
    """Cluster bootstrap over withheld components -> pooled DTI and 95% CI."""
    rng = np.random.default_rng(seed)
    T_c, G_c, M_c = terms["T_c"], terms["G_c"], terms["M_c"]
    n_pred = terms["n_pred"]
    ids = component_ids
    out = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(ids, size=len(ids), replace=True)
        T = T_c[pick].sum()
        G = G_c[pick].sum()
        M = M_c[pick].sum()
        FP = max(n_pred - M, 0.0)
        FN = G - T
        out[b] = T / (T + ALPHA * FP + BETA * FN) if T > 0 else 0.0
    lo, hi = np.percentile(out, [2.5, 97.5])
    return dict(mean=float(out.mean()), lo=float(lo), hi=float(hi))
