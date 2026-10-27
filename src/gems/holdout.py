"""Hide-and-recover holdout (spatially blocked, fail-closed).

Protocol: withhold whole fault segments (8-connected components of the
catalogue) grouped into spatial blocks; derive every catalogue-based
feature only from the VISIBLE faults; mask visible faults pixel-exactly;
score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel) of the
candidate against the withheld segments.  A 5 px buffer ring around
visible faults is excluded from the withheld truth to avoid ambiguity.

Every number produced here is HOLDOUT-DTI (this evaluator, version
GEMSDOESASS2-HRv1), never a leaderboard score.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, label

from .metric import bootstrap_dti, dti_binary, per_component_terms

EVALUATOR_VERSION = "GEMSDOESASS2-HRv1"
N_FOLDS = 4
BLOCK_PX = 400  # 40 km spatial blocks


def component_folds(cat_mask: np.ndarray, n_folds: int = N_FOLDS,
                    block_px: int = BLOCK_PX, seed: int = 20261027):
    """Label catalogue components; assign each to a fold by spatial block."""
    labels, n = label(cat_mask, structure=np.ones((3, 3), int))
    idx = np.arange(1, n + 1)
    # component centroid block
    rs, cs = np.where(cat_mask)
    lab = labels[rs, cs]
    sum_r = np.bincount(lab, weights=rs, minlength=n + 1)[1:]
    sum_c = np.bincount(lab, weights=cs, minlength=n + 1)[1:]
    cnt = np.bincount(lab, minlength=n + 1)[1:]
    cr, cc = sum_r / cnt, sum_c / cnt
    bx, by = (cr // block_px).astype(int), (cc // block_px).astype(int)
    rng = np.random.default_rng(seed)
    # each spatial block goes entirely to one fold (blocked CV)
    blocks = {}
    for b in set(zip(bx, by)):
        blocks[b] = rng.integers(0, n_folds)
    fold_of = np.array([blocks[(x, y)] for x, y in zip(bx, by)])
    return labels, idx, fold_of


def run_holdout(make_dots, cat_mask: np.ndarray, footprint: np.ndarray,
                n_folds: int = N_FOLDS, buffer_px: float = 5.0,
                n_boot: int = 400):
    """make_dots(visible_mask) -> binary dot raster built from visible only.

    Returns per-fold DTI, pooled mean, bootstrap CI, withheld positives.
    """
    labels, idx, fold_of = component_folds(cat_mask, n_folds)
    folds = []
    boots = []
    withheld_total = 0
    for f in range(n_folds):
        withheld_ids = idx[fold_of == f]
        withheld = np.isin(labels, withheld_ids)
        visible = cat_mask & ~withheld
        d_vis = distance_transform_edt(~visible)
        truth = withheld & (d_vis > buffer_px) & footprint
        score_mask = footprint & ~visible  # mask visible pixel-exactly
        dots = make_dots(visible) & score_mask
        res = dti_binary(dots, truth, score_mask)
        # cluster bootstrap over withheld components
        tl = np.where(truth, labels, 0)
        terms = per_component_terms(dots, truth, tl, labels.max())
        comp_ids = np.unique(tl[tl > 0])
        bs = bootstrap_dti(terms, comp_ids, n_boot=n_boot) if len(comp_ids) else None
        folds.append(res)
        boots.append(bs)
        withheld_total += int(truth.sum())
    dtis = [r["dti"] for r in folds]
    lo = float(np.mean([b["lo"] for b in boots if b]))
    hi = float(np.mean([b["hi"] for b in boots if b]))
    return dict(evaluator=EVALUATOR_VERSION, n_folds=n_folds,
                fold_dti=dtis, mean_dti=float(np.mean(dtis)),
                ci95=[lo, hi], withheld_positives=withheld_total)
