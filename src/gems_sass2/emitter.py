"""Submodular Lazy-Greedy DW-Tversky CELF Emitters (Isotropic & Strike-Stepping Single-Strand).

1. `emit_celf`: Exact lazy-greedy submodular optimization of expected `TP_w` under the
   competition's 300 m (`R = 3.0 px`) triangular kernel `k(d) = max(1 - d/3.0, 0)`.
2. `emit_anisotropic_single_strand_celf` (`SASS2-XGHF` EXP-3): Uses local structure-tensor
   fault strike `(cos 2*theta, sin 2*theta)` and coherence `coh` so broad geophysical fault
   halos cannot waste two parallel rows of dots across a single fault strand (cross-strike
   saturation radius `r_perp = 4.2 px` where `coh > 0.30`), while stepping along-strike at
   optimal 300 m kernel intervals (`r_par = 3.05 px`) and reallocating saved budget into
   blind intrabasin hydrothermal conduits and step-over relays.
"""

from __future__ import annotations

import heapq

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from .metric import ALPHA, BETA, RADIUS_PX


def _sample_bilinear(arr: np.ndarray, yy: np.ndarray, xx: np.ndarray) -> np.ndarray:
    h, w = arr.shape
    yc = np.clip(yy, 0.0, h - 1.001)
    xc = np.clip(xx, 0.0, w - 1.001)
    y0 = yc.astype(np.int32)
    x0 = xc.astype(np.int32)
    dy = yc - y0
    dx = xc - x0
    v00 = arr[y0, x0]
    v01 = arr[y0, x0 + 1]
    v10 = arr[y0 + 1, x0]
    v11 = arr[y0 + 1, x0 + 1]
    return (v00 * (1.0 - dy) * (1.0 - dx) + v01 * (1.0 - dy) * dx + v10 * dy * (1.0 - dx) + v11 * dy * dx).astype(
        np.float32
    )


def sharpen_ridge_crest(prob: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Oriented 1-px cross-strike Hessian crest concentration (centers smooth ridges onto fault axis)."""
    p = np.where(foot & np.isfinite(prob), prob, 0.0).astype(np.float32)
    ps = gaussian_filter(p, sigma=1.0, mode="nearest")
    axx = gaussian_filter(p, sigma=1.2, order=(0, 2), mode="nearest")
    ayy = gaussian_filter(p, sigma=1.2, order=(2, 0), mode="nearest")
    axy = gaussian_filter(p, sigma=1.2, order=(1, 1), mode="nearest")
    phi = 0.5 * np.arctan2(2.0 * axy, (axx - ayy) + 1e-12)
    nx1, ny1 = np.cos(phi).astype(np.float32), np.sin(phi).astype(np.float32)
    c1 = np.abs(axx * nx1 * nx1 + 2.0 * axy * nx1 * ny1 + ayy * ny1 * ny1)
    c2 = np.abs(axx * (-ny1) * (-ny1) + 2.0 * axy * (-ny1) * nx1 + ayy * nx1 * nx1)
    use_perp = c2 > c1
    nx = np.where(use_perp, -ny1, nx1).astype(np.float32)
    ny = np.where(use_perp, nx1, ny1).astype(np.float32)
    del axx, ayy, axy, phi, nx1, ny1, c1, c2, use_perp

    h, w = p.shape
    gy, gx = np.meshgrid(np.arange(h, dtype=np.float32), np.arange(w, dtype=np.float32), indexing="ij")
    step = 1.35
    p_plus = _sample_bilinear(ps, gy + step * ny, gx + step * nx)
    p_minus = _sample_bilinear(ps, gy - step * ny, gx - step * nx)
    del gy, gx, nx, ny
    flank_mean = 0.5 * (p_plus + p_minus)
    crest_prom = np.clip((ps - flank_mean) / (ps + 1e-4), 0.0, 1.0)
    is_local_crest = ((ps >= p_plus - 1e-6) & (ps >= p_minus - 1e-6)).astype(np.float32)
    out = p * (0.28 + 0.47 * np.sqrt(crest_prom) + 0.25 * is_local_crest)
    out[~foot] = 0.0
    return out.astype(np.float32)

OFFSETS_R3 = [
    (dy, dx, float(1.0 - np.hypot(dy, dx) / RADIUS_PX))
    for dy in range(-2, 3)
    for dx in range(-2, 3)
    if np.hypot(dy, dx) < RADIUS_PX
]

OFFSETS_ANISO = [
    (dy, dx, float(np.hypot(dy, dx)))
    for dy in range(-4, 5)
    for dx in range(-4, 5)
    if np.hypot(dy, dx) <= 4.3
]


def emit_celf(
    prob: np.ndarray,
    valid_mask: np.ndarray,
    known_mask: np.ndarray,
    b_collar_px: float = 2.0,
    max_dots: int = 37_654,
    min_prob: float = 1e-4,
    max_candidates: int = 260_000,
) -> np.ndarray:
    """Exact lazy-greedy submodular CELF emitter under 300 m triangular kernel."""
    h, w = prob.shape
    d_known = (
        distance_transform_edt(~known_mask)
        if np.any(known_mask)
        else np.full((h, w), 999.0, dtype=np.float32)
    )
    eligible = valid_mask & (d_known > b_collar_px)
    field = np.where(valid_mask & ~known_mask, np.clip(prob, 0.0, 1.0), 0.0).astype(np.float32)

    cand_yx = np.nonzero(eligible & (field >= min_prob))
    ys, xs = cand_yx[0], cand_yx[1]
    if ys.size == 0 or max_dots <= 0:
        return np.zeros((h, w), dtype=bool)

    if ys.size > max_candidates:
        vals = field[ys, xs]
        keep = np.argpartition(vals, -max_candidates)[-max_candidates:]
        ys, xs = ys[keep], xs[keep]

    cov = np.zeros((h, w), dtype=np.float32)
    if np.any(known_mask):
        cov[d_known < RADIUS_PX] = np.maximum(
            0.0, 1.0 - d_known[d_known < RADIUS_PX] / RADIUS_PX
        ).astype(np.float32)

    def _gain(y: int, x: int) -> float:
        g = 0.0
        for dy, dx, kw in OFFSETS_R3:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                f_v = float(field[ny, nx])
                if f_v > 0.0:
                    rem = kw - float(cov[ny, nx])
                    if rem > 0.0:
                        g += f_v * rem
        return g

    heap: list[tuple[float, int, int, int]] = []
    for idx in range(ys.size):
        y, x = int(ys[idx]), int(xs[idx])
        g0 = _gain(y, x)
        if g0 > 1e-7:
            heap.append((-g0, idx, y, x))
    heapq.heapify(heap)

    out = np.zeros((h, w), dtype=bool)
    placed = 0
    while heap and placed < max_dots:
        neg_g, idx, y, x = heapq.heappop(heap)
        if out[y, x]:
            continue
        cur_g = _gain(y, x)
        if cur_g <= 1e-7:
            continue
        next_upper = -heap[0][0] if heap else 0.0
        if cur_g >= next_upper - 1e-9:
            out[y, x] = True
            placed += 1
            for dy, dx, kw in OFFSETS_R3:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and kw > cov[ny, nx]:
                    cov[ny, nx] = kw
        else:
            heapq.heappush(heap, (-cur_g, idx, y, x))
    return out


def emit_anisotropic_single_strand_celf(
    prob: np.ndarray,
    cos2theta: np.ndarray,
    sin2theta: np.ndarray,
    coherence: np.ndarray,
    valid_mask: np.ndarray,
    known_mask: np.ndarray,
    b_collar_px: float = 2.0,
    max_dots: int = 37_654,
    r_along_px: float = 3.15,
    r_across_px: float = 4.25,
    min_sep_px: float = 2.65,
    min_prob: float = 1e-4,
    max_candidates: int = 280_000,
    initial_mask: np.ndarray | None = None,
) -> np.ndarray:
    """Anisotropic strike-stepping submodular CELF emitter (`SASS2-XGHF` EXP-3).

    Supports `initial_mask` for two-horizon residual submodular cover: Stage B starts
    from the exact 300 m kernel coverage & exclusion halo of Stage A (`initial_mask`)
    and adds up to `max_dots` NEW non-overlapping off-catalogue conduit dots.
    """
    h, w = prob.shape
    d_known = (
        distance_transform_edt(~known_mask).astype(np.float32)
        if np.any(known_mask)
        else np.full((h, w), 999.0, dtype=np.float32)
    )
    eligible = valid_mask & (d_known > b_collar_px)
    field = np.where(valid_mask & ~known_mask, np.clip(prob, 0.0, 1.0), 0.0).astype(np.float32)

    out = np.zeros((h, w), dtype=bool)
    cov = np.zeros((h, w), dtype=np.float32)
    blocked = np.zeros((h, w), dtype=bool)
    if np.any(known_mask):
        near_k = d_known < RADIUS_PX
        cov[near_k] = np.maximum(0.0, 1.0 - d_known[near_k] / RADIUS_PX).astype(np.float32)

    if initial_mask is not None and np.any(initial_mask):
        init_b = np.asarray(initial_mask, dtype=bool) & eligible
        out |= init_b
        if np.any(init_b):
            d_init = distance_transform_edt(~init_b).astype(np.float32)
            near_i = d_init < RADIUS_PX
            cov[near_i] = np.maximum(cov[near_i], 1.0 - d_init[near_i] / RADIUS_PX)
            blocked |= d_init < min_sep_px
            del d_init

    cand_yx = np.nonzero(eligible & ~out & ~blocked & (field >= min_prob))
    ys, xs = cand_yx[0], cand_yx[1]
    if ys.size == 0 or max_dots <= 0:
        return out

    if ys.size > max_candidates:
        vals = field[ys, xs]
        keep = np.argpartition(vals, -max_candidates)[-max_candidates:]
        ys, xs = ys[keep], xs[keep]

    phi = 0.5 * np.arctan2(sin2theta, cos2theta)
    tx_map = (-np.sin(phi)).astype(np.float32)
    ty_map = np.cos(phi).astype(np.float32)
    del phi
    coh_map = np.clip(coherence, 0.0, 1.0).astype(np.float32)

    def _gain(y: int, x: int) -> float:
        if blocked[y, x]:
            return 0.0
        g = 0.0
        for dy, dx, kw in OFFSETS_R3:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                f_v = float(field[ny, nx])
                if f_v > 0.0:
                    rem = kw - float(cov[ny, nx])
                    if rem > 0.0:
                        g += f_v * rem
        return g

    heap: list[tuple[float, int, int, int]] = []
    for idx in range(ys.size):
        y, x = int(ys[idx]), int(xs[idx])
        g0 = _gain(y, x)
        if g0 > 1e-7:
            heap.append((-g0, idx, y, x))
    heapq.heapify(heap)

    added = 0
    min_sep_sq = min_sep_px * min_sep_px

    while heap and added < max_dots:
        neg_g, idx, y, x = heapq.heappop(heap)
        if out[y, x] or blocked[y, x]:
            continue
        cur_g = _gain(y, x)
        if cur_g <= 1e-7:
            continue
        next_upper = -heap[0][0] if heap else 0.0
        if cur_g >= next_upper - 1e-9:
            out[y, x] = True
            added += 1
            ty_loc = float(ty_map[y, x])
            tx_loc = float(tx_map[y, x])
            c_loc = float(coh_map[y, x])
            r_par = RADIUS_PX + c_loc * (r_along_px - RADIUS_PX)
            r_perp = RADIUS_PX + c_loc * (r_across_px - RADIUS_PX)

            for dy, dx, dist_euc in OFFSETS_ANISO:
                ny, nx = y + dy, x + dx
                if not (0 <= ny < h and 0 <= nx < w):
                    continue
                if dy * dy + dx * dx < min_sep_sq:
                    blocked[ny, nx] = True
                s_par = dy * ty_loc + dx * tx_loc
                s_perp = -dy * tx_loc + dx * ty_loc
                d_aniso = float(np.hypot(s_par / r_par, s_perp / r_perp))
                if d_aniso < 1.0:
                    kw_aniso = 1.0 - d_aniso
                    if kw_aniso > cov[ny, nx]:
                        cov[ny, nx] = kw_aniso
                if dist_euc < RADIUS_PX:
                    kw_euc = 1.0 - dist_euc / RADIUS_PX
                    if kw_euc > cov[ny, nx]:
                        cov[ny, nx] = kw_euc
        else:
            heapq.heappush(heap, (-cur_g, idx, y, x))
    return out
