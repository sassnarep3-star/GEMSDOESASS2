"""Bit-exact Spatially-Blocked Hide-and-Recover & Off-Catalogue SGMC Holdout Engine.

Matches `GEMSDOE32-HIDE-RECOVER-v3.0` (`n=22,232` withheld catalogue positives across
8 spatially-blocked cells = 4 quadrants x draws 20/21, 1.5 km collar, 1.2 km border erosion,
visible-only `B` masking, 256-block spatial cluster bootstrap 95% CI) and
`GEMSDOE32-SGMC-CAL-v3.0` (`n=62,703` off-catalogue USGS SGMC faults >300 m outside `labels.tif`).

Fixes shared template issue `IR-TEMPLATE-STATIC-VS-FOLD-02`:
  - Persists deterministic 256-block `(tp, fp, fn)` vectors and bootstrap draws on BOTH
    `evaluate_hide_and_recover` and `evaluate_sgmc_with_ci`, guaranteeing exact paired
    spatial-block bootstrap Delta-DTI and 95% CIs across any pair of runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, binary_erosion, distance_transform_edt, label

from .metric import ALPHA, BETA, EPS, kernel

FOLD_NAMES = ("NW", "NE", "SW", "SE")
FOLDS = (0, 1, 2, 3)
DRAWS = (20, 21)
COLLAR_PX = 15       # 1.5 km spatial buffer between train and test quadrants
DOMAIN_ERODE = 12    # 1.2 km boundary erosion
NEAR_LABEL_PX = 3    # 300 m kernel radius around known catalogue faults
ESTIMATED_LB_HIDDEN_TRUTH_PX = 12691.0
HIDE_RECOVER_EVALUATOR_VERSION = "GEMSDOE32-HIDE-RECOVER-v3.0"
SGMC_EVALUATOR_VERSION = "GEMSDOE32-SGMC-CAL-v3.0"


def quadrant_ids(footprint: np.ndarray) -> np.ndarray:
    footprint = np.asarray(footprint, bool)
    yy, xx = np.nonzero(footprint)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    h, w = footprint.shape
    gy, gx = np.ogrid[:h, :w]
    q = np.full((h, w), -1, np.int8)
    q[(gy < ym) & (gx < xm) & footprint] = 0
    q[(gy < ym) & (gx >= xm) & footprint] = 1
    q[(gy >= ym) & (gx < xm) & footprint] = 2
    q[(gy >= ym) & (gx >= xm) & footprint] = 3
    return q


@dataclass
class PreparedCell:
    key: str
    fold: int
    seed: int
    bbox: tuple[slice, slice]
    active_sub: np.ndarray
    truth_coords: tuple[np.ndarray, np.ndarray]
    k_dg_sub: np.ndarray
    n_truth: int
    visible_sub: np.ndarray
    d_vis_sub: np.ndarray
    visible_full: np.ndarray


@dataclass
class HoldoutContext:
    foot: np.ndarray
    labels: np.ndarray
    sgmc_off: np.ndarray
    quad: np.ndarray
    quad_bboxes: dict[int, tuple[slice, slice]]
    collars: dict[int, np.ndarray]
    cells: list[PreparedCell]
    sgmc_truth_coords: tuple[np.ndarray, np.ndarray]
    sgmc_k_dg: np.ndarray
    sgmc_n_truth: int


def _pick_components(rng: np.random.Generator, comp_size: np.ndarray, ids: np.ndarray, target_px: float) -> np.ndarray:
    if ids.size == 0:
        return ids
    perm = rng.permutation(ids)
    cum = np.cumsum(comp_size[perm])
    k = int(np.searchsorted(cum, target_px)) + 1
    return perm[: min(k, perm.size)]


def load_holdout_context(ddir: Path, hide_frac: float = 0.20) -> HoldoutContext:
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ddir / "labels.tif") as ds:
        a = ds.read(1)
        labels = np.isfinite(a) & (a > 0) & foot
    with rasterio.open(ddir / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgm = ds.read(1) > 0

    near = binary_dilation(labels, iterations=NEAR_LABEL_PX)
    sgmc_off = sgm & ~labels & ~near & foot

    quad = quadrant_ids(foot)
    comp, n_comp = label(labels, structure=np.ones((3, 3), int))
    comp_size = np.bincount(comp.ravel(), minlength=n_comp + 1)
    all_ids = np.arange(1, n_comp + 1)

    quad_bboxes: dict[int, tuple[slice, slice]] = {}
    collars: dict[int, np.ndarray] = {}
    domains: dict[int, np.ndarray] = {}
    for fold in FOLDS:
        q = quad == fold
        rows = np.flatnonzero(q.any(axis=1))
        cols = np.flatnonzero(q.any(axis=0))
        r0 = max(0, int(rows[0]) - 6)
        r1 = min(foot.shape[0], int(rows[-1]) + 7)
        c0 = max(0, int(cols[0]) - 6)
        c1 = min(foot.shape[1], int(cols[-1]) + 7)
        quad_bboxes[fold] = (slice(r0, r1), slice(c0, c1))
        collars[fold] = binary_dilation(q, structure=np.ones((3, 3), bool), iterations=COLLAR_PX) & foot
        domains[fold] = binary_erosion(q, iterations=DOMAIN_ERODE)

    cells: list[PreparedCell] = []
    for seed in DRAWS:
        for fold in FOLDS:
            rng = np.random.default_rng(10_000 * (seed + 1) + fold)
            q = quad == fold
            collar = collars[fold]
            domain = domains[fold]
            touch_collar = np.isin(all_ids, np.unique(comp[collar & labels]))
            in_test = np.isin(all_ids, np.unique(comp[q & labels]))
            test_ids = all_ids[in_test]
            train_ids = all_ids[~touch_collar]
            hid_test = _pick_components(rng, comp_size, test_ids, hide_frac * float((labels & q).sum()))
            hid_train = _pick_components(rng, comp_size, train_ids, hide_frac * float(comp_size[train_ids].sum()))
            hidden_full = np.isin(comp, hid_test)
            hidden_train = np.isin(comp, hid_train)
            visible = labels & ~hidden_full & ~hidden_train

            sl = quad_bboxes[fold]
            active_sub = domain[sl] & ~visible[sl]
            truth_sub = (hidden_full[sl] & domain[sl]) & active_sub
            t_coords = np.nonzero(truth_sub)
            n_t = int(t_coords[0].size)
            dg_sub = distance_transform_edt(~truth_sub)
            k_dg_sub = kernel(dg_sub)
            vis_sub = visible[sl].copy()
            d_vis_sub = (
                distance_transform_edt(~vis_sub).astype(np.float32)
                if vis_sub.any()
                else np.full(vis_sub.shape, 999.0, dtype=np.float32)
            )
            cells.append(
                PreparedCell(
                    key=f"draw{seed}_fold{fold}",
                    fold=fold,
                    seed=seed,
                    bbox=sl,
                    active_sub=active_sub,
                    truth_coords=t_coords,
                    k_dg_sub=k_dg_sub,
                    n_truth=n_t,
                    visible_sub=vis_sub,
                    d_vis_sub=d_vis_sub,
                    visible_full=visible.copy(),
                )
            )

    sgmc_truth = sgmc_off & foot & ~labels
    sgmc_truth_coords = np.nonzero(sgmc_truth)
    sgmc_n_truth = int(sgmc_truth_coords[0].size)
    sgmc_k_dg = kernel(distance_transform_edt(~sgmc_truth))

    return HoldoutContext(
        foot=foot,
        labels=labels,
        sgmc_off=sgmc_off,
        quad=quad,
        quad_bboxes=quad_bboxes,
        collars=collars,
        cells=cells,
        sgmc_truth_coords=sgmc_truth_coords,
        sgmc_k_dg=sgmc_k_dg,
        sgmc_n_truth=sgmc_n_truth,
    )


def spatial_block_index(ys: np.ndarray, xs: np.ndarray, shape: tuple[int, int], grid_n: int = 16) -> np.ndarray:
    h, w = shape
    by = np.minimum((ys * grid_n) // h, grid_n - 1)
    bx = np.minimum((xs * grid_n) // w, grid_n - 1)
    return (by * grid_n + bx).astype(np.int32)


def cluster_bootstrap_pooled_dti(
    tp_vec: np.ndarray,
    fp_vec: np.ndarray,
    fn_vec: np.ndarray,
    active_blocks: np.ndarray,
    n_boot: int = 1000,
    seed: int = 20261026,
) -> tuple[float, list[float], np.ndarray]:
    tp_a = tp_vec[active_blocks]
    fp_a = fp_vec[active_blocks]
    fn_a = fn_vec[active_blocks]
    tot_tp = float(tp_a.sum())
    tot_fp = float(fp_a.sum())
    tot_fn = float(fn_a.sum())
    pooled = float(tot_tp / (tot_tp + ALPHA * tot_fp + BETA * tot_fn + EPS))
    k = int(active_blocks.size)
    if k == 0:
        return 0.0, [0.0, 0.0], np.zeros(n_boot, dtype=np.float64)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(n_boot, k))
    btp = tp_a[idx].sum(axis=1)
    bfp = fp_a[idx].sum(axis=1)
    bfn = fn_a[idx].sum(axis=1)
    boots = btp / (btp + ALPHA * bfp + BETA * bfn + EPS)
    ci95 = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
    return pooled, ci95, boots


def paired_bootstrap_delta(boots_a: np.ndarray, boots_b: np.ndarray) -> dict:
    diff = np.asarray(boots_a, dtype=np.float64) - np.asarray(boots_b, dtype=np.float64)
    return {
        "mean_delta": float(diff.mean()),
        "ci95": [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))],
        "prob_gt_zero": float((diff > 0.0).mean()),
        "statistically_positive_95": bool(np.percentile(diff, 2.5) > 0.0),
    }


def evaluate_hide_and_recover(
    pred_or_cells: np.ndarray | dict[str, np.ndarray],
    ctx: HoldoutContext,
    b_visible_px: float = 2.0,
    detach_min_px: float = 6.0,
    grid_n: int = 16,
    n_boot: int = 1000,
    seed: int = 20261026,
    name: str = "candidate",
) -> dict:
    """Exact Protocol Rule 2 leak-free Hide-and-Recover Pooled DTI + Detached-600m blind-fault DTI."""
    h, w = ctx.foot.shape
    n_blocks = grid_n * grid_n
    tp_blk = np.zeros(n_blocks, dtype=np.float64)
    fp_blk = np.zeros(n_blocks, dtype=np.float64)
    fn_blk = np.zeros(n_blocks, dtype=np.float64)

    tp_det = np.zeros(n_blocks, dtype=np.float64)
    fp_det = np.zeros(n_blocks, dtype=np.float64)
    fn_det = np.zeros(n_blocks, dtype=np.float64)
    n_det_pos = 0

    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(spatial_block_index(fy, fx, (h, w), grid_n))

    is_cell_dict = isinstance(pred_or_cells, dict)
    base_mask = None if is_cell_dict else (np.asarray(pred_or_cells, bool) & ctx.foot)

    folds: dict[str, dict] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        r0, c0 = int(sl[0].start), int(sl[1].start)
        if is_cell_dict:
            raw_cell = np.asarray(pred_or_cells[cell.key], bool)
            sub_in = raw_cell[sl] if raw_cell.shape == (h, w) else raw_cell
        else:
            sub_in = base_mask[sl]

        p_sub = sub_in & cell.active_sub
        if b_visible_px > 0.0:
            p_sub = p_sub & (cell.d_vis_sub > b_visible_px)

        n_emit = int(p_sub.sum())
        n_t = cell.n_truth
        ty_sub, tx_sub = cell.truth_coords
        t_blk = spatial_block_index(ty_sub + r0, tx_sub + c0, (h, w), grid_n)

        if n_t == 0:
            folds[cell.key] = {"dti": 0.0, "tp": 0.0, "fp": float(n_emit), "fn": 0.0, "n_truth": 0, "emitted": n_emit}
            continue

        if n_emit == 0:
            np.add.at(fn_blk, t_blk, 1.0)
            folds[cell.key] = {"dti": 0.0, "tp": 0.0, "fp": 0.0, "fn": float(n_t), "n_truth": n_t, "emitted": 0}
        else:
            dp_sub = distance_transform_edt(~p_sub)
            t_cred = kernel(dp_sub[cell.truth_coords]).astype(np.float64)
            tp = float(t_cred.sum())
            fn = float(n_t) - tp
            np.add.at(tp_blk, t_blk, t_cred)
            np.add.at(fn_blk, t_blk, 1.0 - t_cred)

            py_sub, px_sub = np.nonzero(p_sub)
            p_blk = spatial_block_index(py_sub + r0, px_sub + c0, (h, w), grid_n)
            fp_weights = (1.0 - cell.k_dg_sub[p_sub]).astype(np.float64)
            fp = float(fp_weights.sum())
            np.add.at(fp_blk, p_blk, fp_weights)

            dti_c = float(tp / (tp + ALPHA * fp + BETA * fn + EPS))
            folds[cell.key] = {
                "dti": dti_c,
                "coverage": float(tp / n_t),
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "n_truth": n_t,
                "emitted": n_emit,
            }

        det_keep = cell.d_vis_sub[ty_sub, tx_sub] >= detach_min_px
        if det_keep.any():
            dty, dtx = ty_sub[det_keep], tx_sub[det_keep]
            n_det_pos += int(dty.size)
            det_truth = np.zeros(cell.active_sub.shape, dtype=bool)
            det_truth[dty, dtx] = True
            k_dg_det = kernel(distance_transform_edt(~det_truth))
            p_det = p_sub & (cell.d_vis_sub >= (detach_min_px - 3.0))
            dt_blk = spatial_block_index(dty + r0, dtx + c0, (h, w), grid_n)
            if p_det.any():
                dp_det = distance_transform_edt(~p_det)
                tc_det = kernel(dp_det[dty, dtx]).astype(np.float64)
                np.add.at(tp_det, dt_blk, tc_det)
                np.add.at(fn_det, dt_blk, 1.0 - tc_det)
                py_d, px_d = np.nonzero(p_det)
                p_blk_d = spatial_block_index(py_d + r0, px_d + c0, (h, w), grid_n)
                np.add.at(fp_det, p_blk_d, (1.0 - k_dg_det[p_det]).astype(np.float64))
            else:
                np.add.at(fn_det, dt_blk, 1.0)

    pooled, ci95, boots = cluster_bootstrap_pooled_dti(tp_blk, fp_blk, fn_blk, active_blocks, n_boot=n_boot, seed=seed)
    det_pooled, det_ci95, det_boots = cluster_bootstrap_pooled_dti(
        tp_det, fp_det, fn_det, active_blocks, n_boot=n_boot, seed=seed
    )
    n_withheld = int(sum(v["n_truth"] for v in folds.values()))
    per_quad = {
        FOLD_NAMES[f]: float(np.mean([folds[f"draw{ds}_fold{f}"]["dti"] for ds in DRAWS]))
        for f in FOLDS
    }
    return {
        "candidate_id": name,
        "evaluator_version": HIDE_RECOVER_EVALUATOR_VERSION,
        "score_label": "HOLDOUT-DTI",
        "mode": "fold_local_visible_only_oof" if is_cell_dict else "static_raster_censored_if_b2",
        "b_visible_px": float(b_visible_px),
        "n_withheld_positives": n_withheld,
        "n_spatial_clusters": int(active_blocks.size),
        "n_bootstrap_reps": int(n_boot),
        "pooled_dti": pooled,
        "ci95_cluster_bootstrap": ci95,
        "fold_mean_dti": float(np.mean([v["dti"] for v in folds.values()])),
        "per_quadrant_dti": per_quad,
        "detached_600m": {
            "n_withheld_positives": n_det_pos,
            "pooled_dti": det_pooled,
            "ci95_cluster_bootstrap": det_ci95,
            "_boots": det_boots,
        },
        "folds": folds,
        "_block_totals": (tp_blk, fp_blk, fn_blk, active_blocks),
        "_boots": boots,
    }


def evaluate_sgmc_with_ci(
    mask: np.ndarray,
    ctx: HoldoutContext,
    grid_n: int = 16,
    n_boot: int = 1000,
    seed: int = 20261026,
    name: str = "candidate",
) -> dict:
    """Off-catalogue USGS SGMC DTI (62,703 fault pixels >300 m outside `labels.tif`) with 256-block CI."""
    h, w = ctx.foot.shape
    mask = np.asarray(mask, bool) & ctx.foot & ~ctx.labels
    n_blocks = grid_n * grid_n
    tp_blk = np.zeros(n_blocks, dtype=np.float64)
    fp_blk = np.zeros(n_blocks, dtype=np.float64)
    fn_blk = np.zeros(n_blocks, dtype=np.float64)

    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(spatial_block_index(fy, fx, (h, w), grid_n))

    ty, tx = ctx.sgmc_truth_coords
    t_blk = spatial_block_index(ty, tx, (h, w), grid_n)
    if mask.any() and ctx.sgmc_n_truth > 0:
        dp = distance_transform_edt(~mask)
        t_cred = kernel(dp[ctx.sgmc_truth_coords]).astype(np.float64)
        np.add.at(tp_blk, t_blk, t_cred)
        np.add.at(fn_blk, t_blk, 1.0 - t_cred)
        py, px = np.nonzero(mask)
        p_blk = spatial_block_index(py, px, (h, w), grid_n)
        fp_w = (1.0 - ctx.sgmc_k_dg[mask]).astype(np.float64)
        np.add.at(fp_blk, p_blk, fp_w)
    else:
        np.add.at(fn_blk, t_blk, 1.0)

    raw_pooled, raw_ci95, raw_boots = cluster_bootstrap_pooled_dti(
        tp_blk, fp_blk, fn_blk, active_blocks, n_boot=n_boot, seed=seed
    )

    r_prev = ESTIMATED_LB_HIDDEN_TRUTH_PX / max(float(ctx.sgmc_n_truth), 1.0)
    emit_blk = np.zeros(n_blocks, dtype=np.float64)
    if mask.any():
        py, px = np.nonzero(mask)
        np.add.at(emit_blk, spatial_block_index(py, px, (h, w), grid_n), 1.0)
    tp_cal_a = tp_blk[active_blocks] * r_prev
    fn_cal_a = fn_blk[active_blocks] * r_prev
    emit_a = emit_blk[active_blocks]

    tot_tp_c = float(tp_cal_a.sum())
    tot_fn_c = float(fn_cal_a.sum())
    tot_fp_c = max(0.0, float(emit_a.sum()) - tot_tp_c)
    cal_pooled = float(tot_tp_c / (ALPHA * (tot_tp_c + tot_fp_c) + BETA * (tot_tp_c + tot_fn_c) + EPS))

    rng = np.random.default_rng(seed)
    k = int(active_blocks.size)
    idx = rng.integers(0, k, size=(n_boot, k))
    btp = tp_cal_a[idx].sum(axis=1)
    bfn = fn_cal_a[idx].sum(axis=1)
    bemit = emit_a[idx].sum(axis=1)
    bfp = np.maximum(0.0, bemit - btp)
    cal_boots = btp / (ALPHA * (btp + bfp) + BETA * (btp + bfn) + EPS)
    cal_ci95 = [float(np.percentile(cal_boots, 2.5)), float(np.percentile(cal_boots, 97.5))]

    return {
        "candidate_id": name,
        "evaluator_version": SGMC_EVALUATOR_VERSION,
        "score_label": "HOLDOUT-DTI",
        "n_withheld_positives": int(ctx.sgmc_n_truth),
        "n_emitted_off_catalogue": int(mask.sum()),
        "n_spatial_clusters": k,
        "n_bootstrap_reps": int(n_boot),
        "sgmc_raw_pooled_dti": raw_pooled,
        "sgmc_raw_ci95": raw_ci95,
        "sgmc_prevalence_calibrated_dti": cal_pooled,
        "sgmc_calibrated_ci95": cal_ci95,
        "_raw_boots": raw_boots,
        "_cal_boots": cal_boots,
    }
