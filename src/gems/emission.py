"""Dotted emission: greedy top-score dot placement with minimum separation.

Rationale (from the pooled-DTI algebra, see knowledge/01): a binary dot
costs at most 0.2 FP-weight but earns triangular-kernel credit over a 3 px
radius, so sparse dots that tile high-prior corridors dominate continuous
maps under alpha=0.2 / beta=0.8.  The 0.2778 champion is exactly such a
dot set (37,654 dots, B=2 catalogue prune).

This repo's emission differs from the registry lattices: dots are placed on
SRAC surface maxima with Chebyshev separation 2 px (not a D1.5/D2.8
resampled lattice, not Poisson-disc 300 m).
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt


def greedy_dots(surface: np.ndarray, allowed: np.ndarray, n_dots: int,
                sep_px: int = 2) -> np.ndarray:
    """Pick up to n_dots local maxima with Chebyshev min separation sep_px."""
    h, w = surface.shape
    s = np.where(allowed, surface, 0.0).ravel()
    order = np.argsort(-s)
    # candidate cut: keep enough positive candidates
    pos = order[s[order] > 0]
    occupied = np.zeros((h, w), dtype=bool)
    out = np.zeros((h, w), dtype=bool)
    k = sep_px
    taken = 0
    for flat in pos:
        if taken >= n_dots:
            break
        r, c = divmod(int(flat), w)
        if occupied[r, c]:
            continue
        out[r, c] = True
        taken += 1
        r0, r1 = max(0, r - k), min(h, r + k + 1)
        c0, c1 = max(0, c - k), min(w, c + k + 1)
        occupied[r0:r1, c0:c1] = True
    return out


def catalogue_prune(dots: np.ndarray, cat_mask: np.ndarray,
                    buffer_px: float = 2.0) -> np.ndarray:
    """B=2 prune: delete every dot within buffer_px of the catalogue.

    Champion lesson (0.2708 -> 0.2778): catalogue pixels are masked at
    scoring time, so dots on/near them waste FP weight for zero credit.
    """
    d = distance_transform_edt(~cat_mask.astype(bool))
    keep = dots & (d > buffer_px)
    return keep
