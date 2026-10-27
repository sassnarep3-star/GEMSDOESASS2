"""Uniqueness gates vs the registry of previously submitted GEMSDOE rasters.

Gate A (surface/dots rank-correlation): |Spearman| <= 0.90 against every
registry raster, computed on a fixed random sample of footprint pixels.
Gate B (dot overlap): <= 70% of our dots within 3 px (Euclidean) of any
single registry raster's dots.
Gate C: sha256 differs from every registry file.
A failure of any gate against any registry raster = DUPLICATE, fail closed.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

from .io_grid import read_band, sha256

SPEARMAN_MAX = 0.90
OVERLAP_MAX = 0.70
OVERLAP_PX = 3.0


def dot_overlap(our_dots: np.ndarray, reg_raster: np.ndarray) -> float:
    reg = np.nan_to_num(reg_raster, nan=0.0) > 0.5
    if reg.sum() == 0 or our_dots.sum() == 0:
        return 0.0
    d = distance_transform_edt(~reg)
    return float((d[our_dots] <= OVERLAP_PX).mean())


def surface_spearman(a: np.ndarray, b: np.ndarray, footprint: np.ndarray,
                     n_sample: int = 200_000, seed: int = 7) -> float:
    rng = np.random.default_rng(seed)
    rows, cols = np.where(footprint)
    pick = rng.choice(len(rows), size=min(n_sample, len(rows)), replace=False)
    av = np.nan_to_num(a, nan=0.0)[rows[pick], cols[pick]]
    bv = np.nan_to_num(b, nan=0.0)[rows[pick], cols[pick]]
    r = spearmanr(av, bv).statistic
    return float(0.0 if np.isnan(r) else r)


def audit_against_registry(our_tif: str, our_dots: np.ndarray,
                           our_surface: np.ndarray, footprint: np.ndarray,
                           registry: list[dict]) -> dict:
    """registry: [{name, path, owner_reported_score}, ...]"""
    rows = []
    ours_sha = sha256(our_tif)
    for item in registry:
        reg = read_band(item["path"])
        ov = dot_overlap(our_dots, reg)
        rho_dots = surface_spearman(our_dots.astype(np.float32), reg, footprint)
        rho_surf = surface_spearman(our_surface, reg, footprint)
        reg_sha = sha256(item["path"])
        rows.append(dict(
            name=item["name"], owner_reported=item.get("owner_reported_score"),
            dot_overlap_3px=round(ov, 4),
            spearman_final=round(rho_dots, 4),
            spearman_surface=round(rho_surf, 4),
            sha256_equal=(reg_sha == ours_sha),
            passes=(ov <= OVERLAP_MAX and abs(rho_dots) <= SPEARMAN_MAX
                    and abs(rho_surf) <= SPEARMAN_MAX and reg_sha != ours_sha)))
    all_pass = all(r["passes"] for r in rows)
    worst = max(rows, key=lambda r: r["dot_overlap_3px"]) if rows else None
    return dict(all_pass=all_pass, worst_overlap=worst, rows=rows,
                gates=dict(spearman_max=SPEARMAN_MAX, overlap_max=OVERLAP_MAX,
                           overlap_px=OVERLAP_PX), our_sha256=ours_sha)
