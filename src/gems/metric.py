"""Pooled Distance-weighted Tversky Index (DTI).

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
