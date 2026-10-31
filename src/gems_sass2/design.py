"""Density-calibrated space-filling prediction design.

Why not a threshold
-------------------
The official metric is

    DTI = T / (0.2 T + 0.2 F + 0.8 |G|)

For a prediction that can only *weakly* localise the target, the marginal value
of painting one more cell is `P(target within 3 px) - 0.2 DTI (1-k)`, which is
positive almost everywhere inside the geophysical survey and slightly higher
where the model is confident.  Clustered top-k emission therefore wastes the FP
budget: it buys depth (which the `max` in TP_w cannot use twice) instead of
breadth (which raises T directly).

The design below allocates a fixed number of points across the domain so that
neighbouring points stay roughly one kernel radius apart, which maximises the
number of distinct target cells covered per predicted cell, and modulates the
local density gently with the model posterior.  It is a jittered/stratified
(Cox) design, the standard space-filling construction.
"""
from __future__ import annotations

import numpy as np


def jittered_design(weight: np.ndarray, allowed: np.ndarray, n_points: int,
                    *, tilt: float = 0.0, seed: int = 0) -> np.ndarray:
    """Boolean mask of ~`n_points` cells: stratified, with a gentle density tilt.

    weight : per-cell score.  It is rank-normalised inside `allowed`, so only
             the *ordering* matters, never the LightGBM calibration.
    allowed: domain (surveyed footprint minus cells that cannot be a target).
    tilt   : 0 = perfectly uniform space-filling design; 1 = density strictly
             proportional to the score.  Values around 0.3-0.6 keep the design
             spread while still banking genuine localisation skill.
    """
    rng = np.random.default_rng(seed)
    h, w = allowed.shape
    area = int(allowed.sum())
    if n_points >= area:
        return allowed.copy()

    # rank-normalise the score over the allowed domain -> values in (0, 1)
    vals = np.where(allowed, weight, np.nan).ravel()
    ok = np.flatnonzero(np.isfinite(vals))
    order = ok[np.argsort(vals[ok], kind="stable")]
    rank = np.zeros(vals.size, np.float32)
    rank[order] = np.linspace(0.0, 1.0, order.size, dtype=np.float32)
    dens = (1.0 - tilt) + tilt * rank.reshape(allowed.shape)
    dens = np.where(allowed, dens, 0.0)

    side = max(2, int(round(np.sqrt(area / max(n_points, 1)))))
    ny, nx = int(np.ceil(h / side)), int(np.ceil(w / side))
    ph, pw = ny * side - h, nx * side - w
    dp = np.pad(dens, ((0, ph), (0, pw))).reshape(ny, side, nx, side).sum(axis=(1, 3))
    ap = np.pad(allowed.astype(np.float32), ((0, ph), (0, pw))).reshape(ny, side, nx, side).sum(axis=(1, 3))
    valid = ap > 0
    if not valid.any():
        return np.zeros((h, w), bool)

    share = np.zeros_like(dp)
    share[valid] = dp[valid] / dp[valid].sum() * n_points
    n_per_block = np.floor(share).astype(np.int32)
    deficit = n_points - int(n_per_block.sum())
    if deficit > 0:
        vy0, vx0 = np.nonzero(valid)
        order_b = np.argsort(-share[valid].ravel())[:deficit]
        for k in order_b:
            n_per_block[vy0[k], vx0[k]] += 1
    n_per_block = np.minimum(n_per_block, ap.astype(np.int32))

    out = np.zeros((h, w), bool)
    vy, vx = np.nonzero(n_per_block > 0)
    for i, j in zip(vy, vx):
        r0, c0 = int(i) * side, int(j) * side
        r1, c1 = min(r0 + side, h), min(c0 + side, w)
        sub_allowed = allowed[r0:r1, c0:c1]
        idx = np.flatnonzero(sub_allowed.ravel())
        if idx.size == 0:
            continue
        k = min(int(n_per_block[i, j]), idx.size)
        prob = dens[r0:r1, c0:c1].ravel()[idx]
        tot = float(prob.sum())
        if tot <= 0:
            choose = rng.choice(idx, size=k, replace=False)
        else:
            keep = prob > 0
            idx, prob = idx[keep], prob[keep]
            k = min(k, idx.size)
            choose = rng.choice(idx, size=k, replace=False, p=prob / prob.sum())
        rr, cc = np.divmod(choose, c1 - c0)
        out[r0 + rr, c0 + cc] = True
    return out
