"""Leak-free spatial LOQO dual-population GBDT + strike-collinearity + d=2.8 kernel-matched allocator."""
from __future__ import annotations

import gc
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score


def bayes_prior_calibrate(p_raw: np.ndarray, pi_train: float, pi_target: float) -> np.ndarray:
    """Exact Bayes prior-shift calibration from training sample prevalence to true spatial prevalence."""
    p = np.clip(np.asarray(p_raw, dtype=np.float64), 1e-6, 1.0 - 1e-6)
    odds_ratio = (pi_target / max(1.0 - pi_target, 1e-9)) / (pi_train / max(1.0 - pi_train, 1e-9))
    num = odds_ratio * p
    cal = num / (num + (1.0 - p))
    return cal.astype(np.float32)


def run_single_feature_canary(
    static_mm: np.memmap,
    mech_fp: np.ndarray,
    feature_names: tuple[str, ...],
    foot: np.ndarray,
    folds: list[dict],
    auc_limit: float = 0.90,
) -> dict:
    """Gate 1 (Rule 4): Test every feature individually on pooled holdout evaluation pixels."""
    eval_active_2d = np.zeros(foot.shape, dtype=bool)
    truth_2d = np.zeros(foot.shape, dtype=bool)
    for f in folds:
        act = foot & f["region"] & (~f["masked_known"])
        eval_active_2d |= act
        truth_2d |= act & f["truth"]

    active_fp = eval_active_2d[foot]
    y_true = truth_2d[foot][active_fp].astype(np.uint8)
    pos_idx = np.flatnonzero(y_true == 1)
    neg_idx = np.flatnonzero(y_true == 0)[::20]
    sub_idx = np.concatenate([pos_idx, neg_idx])
    y_sub = y_true[sub_idx]

    n_static = static_mm.shape[1]
    rows = []
    for j, name in enumerate(feature_names):
        if j < n_static:
            vals = np.asarray(static_mm[:, j], dtype=np.float32)[active_fp][sub_idx]
        else:
            vals = np.asarray(mech_fp[:, j - n_static], dtype=np.float32)[active_fp][sub_idx]
        raw_auc = float(roc_auc_score(y_sub, vals))
        sym_auc = max(raw_auc, 1.0 - raw_auc)
        rows.append({
            "index": j,
            "feature": name,
            "group": "static_physical_hydro" if j < n_static else "fold_visible_mechanics",
            "raw_roc_auc": round(raw_auc, 5),
            "symmetric_roc_auc": round(sym_auc, 5),
            "leaks_gt_0p90": bool(sym_auc > auc_limit),
        })

    worst = max(rows, key=lambda r: r["symmetric_roc_auc"])
    leaking = [r for r in rows if r["leaks_gt_0p90"]]
    return {
        "n_features_tested": len(rows),
        "n_withheld_positives": int(len(pos_idx)),
        "n_sampled_negatives": int(len(neg_idx)),
        "auc_limit": auc_limit,
        "max_symmetric_auc": worst["symmetric_roc_auc"],
        "max_auc_feature": worst["feature"],
        "n_leaking_features": len(leaking),
        "canary_passed": len(leaking) == 0,
        "features": rows,
    }


def _make_hgbt(seed: int) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        loss="log_loss",
        learning_rate=0.065,
        max_iter=180,
        max_leaf_nodes=47,
        max_depth=6,
        min_samples_leaf=100,
        l2_regularization=5.0,
        early_stopping=False,
        random_state=seed,
    )


def _predict_proba_chunked(clf: HistGradientBoostingClassifier, mm: np.memmap, idx: np.ndarray, extra: np.ndarray | None = None, chunk: int = 250_000) -> np.ndarray:
    out = np.empty(len(idx), dtype=np.float32)
    for start in range(0, len(idx), chunk):
        sl = idx[start : start + chunk]
        xb = np.asarray(mm[sl, :], dtype=np.float32)
        if extra is not None:
            xb = np.hstack([xb, extra[sl, :]])
        out[start : start + len(sl)] = clf.predict_proba(xb)[:, 1].astype(np.float32)
    return out


def fit_predict_loqo_experts(
    static_mm: np.memmap,
    mech_fp: np.ndarray,
    foot: np.ndarray,
    quad_2d: np.ndarray,
    visible_2d: np.ndarray,
    deadband_px: int = 80,
    neg_pos_ratio: int = 10,
    pi_target: float = 0.002507,
    seed: int = 20261027,
) -> dict[str, np.ndarray]:
    """Train 4-quadrant spatial LOQO Expert A (zero-catalogue) & Expert B (cross-component mechanics)."""
    n_fp, _ = static_mm.shape
    quad_fp = quad_2d[foot]
    vis_fp = visible_2d[foot]
    d_vis_2d = ndi.distance_transform_edt(~visible_2d).astype(np.float32)
    d_vis_fp = d_vis_2d[foot]
    del d_vis_2d

    oof_a = np.zeros(n_fp, dtype=np.float32)
    oof_b = np.zeros(n_fp, dtype=np.float32)
    fold_aucs = []

    for q in range(4):
        test_q_2d = (quad_2d == q) & foot
        forbidden_2d = ndi.binary_dilation(test_q_2d, iterations=deadband_px)
        train_elig_fp = (~forbidden_2d[foot]) & (quad_fp >= 0)
        del test_q_2d, forbidden_2d

        pos_idx = np.flatnonzero(train_elig_fp & vis_fp)
        # Match exact B=2.0 px off-catalogue inference support so zero collar spike can occur!
        neg_pool = np.flatnonzero(train_elig_fp & (~vis_fp) & (d_vis_fp > 2.0))
        rng = np.random.default_rng(seed + q * 97)
        n_neg = min(len(neg_pool), len(pos_idx) * neg_pos_ratio)
        neg_idx = np.sort(rng.choice(neg_pool, size=n_neg, replace=False))

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([
            np.ones(len(pos_idx), dtype=np.uint8),
            np.zeros(len(neg_idx), dtype=np.uint8),
        ])
        pi_train = float(len(pos_idx) / len(tr_idx))
        te_idx = np.flatnonzero(quad_fp == q)

        X_tr_a = np.asarray(static_mm[tr_idx, :], dtype=np.float32)
        clf_a = _make_hgbt(seed + q * 17)
        clf_a.fit(X_tr_a, y_tr)
        pa_raw = _predict_proba_chunked(clf_a, static_mm, te_idx)
        oof_a[te_idx] = bayes_prior_calibrate(pa_raw, pi_train=pi_train, pi_target=pi_target)

        X_tr_b = np.hstack([X_tr_a, mech_fp[tr_idx, :]]).astype(np.float32, copy=False)
        del X_tr_a
        clf_b = _make_hgbt(seed + 500 + q * 17)
        clf_b.fit(X_tr_b, y_tr)
        del X_tr_b
        pb_raw = _predict_proba_chunked(clf_b, static_mm, te_idx, extra=mech_fp)
        oof_b[te_idx] = bayes_prior_calibrate(pb_raw, pi_train=pi_train, pi_target=pi_target)
        gc.collect()

        yv_q = vis_fp[te_idx]
        if yv_q.any() and (~yv_q).any():
            fold_aucs.append({
                "quadrant": int(q),
                "n_train_pos": int(len(pos_idx)),
                "n_train_neg": int(len(neg_idx)),
                "expert_a_auc_on_q": round(float(roc_auc_score(yv_q, pa_raw)), 4),
                "expert_b_auc_on_q": round(float(roc_auc_score(yv_q, pb_raw)), 4),
            })

    return {
        "oof_expert_a_fp": oof_a,
        "oof_expert_b_fp": oof_b,
        "fold_diagnostics": fold_aucs,
    }


def _tail_exponential_score(p_fp: np.ndarray) -> np.ndarray:
    """Map probabilities monotonically to unit-scale upper-tail exceedance -log(1 - rank_u)."""
    n = len(p_fp)
    u = (rankdata(p_fp, method="average") - 0.5) / float(n)
    return (-np.log(np.maximum(1.0 - u, 1.0 / (n + 1.0)))).astype(np.float32)


def fuse_dual_population(
    p_a_fp: np.ndarray,
    p_b_fp: np.ndarray,
    w_a: float = 0.60,
    w_b: float = 0.40,
    pi_target: float = 0.002507,
) -> np.ndarray:
    """Tail-calibrated Dual-Population synthesis preventing near-catalogue halo dominance."""
    ea = _tail_exponential_score(p_a_fp)
    eb = _tail_exponential_score(p_b_fp)
    # Convex blend in exponential tail log-exceedance + synergistic geometric boost where BOTH fire!
    syn = np.sqrt(np.maximum(ea - 1.5, 0.0) * np.maximum(eb - 1.5, 0.0))
    comb = w_a * ea + w_b * eb + np.float32(0.18) * syn
    # Convert smoothly back to [0, 1] probability scaled to target spatial prevalence
    raw_p = 1.0 - np.exp(-np.clip(comb * 0.35, 0.0, 6.0))
    mean_p = max(float(raw_p.mean()), 1e-8)
    return np.clip(raw_p * (pi_target / mean_p), 0.0, 0.95).astype(np.float32)


def oriented_collinearity_sharpen(
    prob_2d: np.ndarray,
    foot: np.ndarray,
    hanvf_fp: np.ndarray,
    ridge_convex_fp: np.ndarray,
    road_safe_fp: np.ndarray,
    hydro_geophys_prior_fp: np.ndarray | None = None,
    pi_target: float = 0.002507,
) -> np.ndarray:
    """EXP-3: Tight 500 m strike-collinearity centerline sharpening + blind hydrothermal/geophysical corridor prior."""
    H, W = prob_2d.shape
    p = np.where(foot, prob_2d, 0.0).astype(np.float32)
    p_broad = ndi.gaussian_filter(p, sigma=3.0, mode="constant")

    # Tight +/- 2 px (500 m) 8-azimuth line-integral preserves curved scarps without blurring off centerline
    best_line = np.zeros((H, W), dtype=np.float32)
    azimuths_deg = (0.0, 18.0, 38.0, 62.0, 90.0, 118.0, 142.0, 162.0)
    az_weights = (1.02, 1.10, 1.05, 0.94, 0.90, 0.95, 1.07, 1.04)

    for az, aw in zip(azimuths_deg, az_weights):
        rad = np.deg2rad(az)
        dy, dx = -np.cos(rad), np.sin(rad)
        along = np.zeros((H, W), dtype=np.float32)
        w_sum = 0.0
        for step in (-2, -1, 0, 1, 2):
            wt = 1.0 if step == 0 else (0.85 if abs(step) == 1 else 0.65)
            sy, sx = int(round(step * dy)), int(round(step * dx))
            y0_d, y1_d = max(0, sy), min(H, H + sy)
            y0_s, y1_s = max(0, -sy), min(H, H - sy)
            x0_d, x1_d = max(0, sx), min(W, W + sx)
            x0_s, x1_s = max(0, -sx), min(W, W - sx)
            along[y0_d:y1_d, x0_d:x1_d] += np.float32(wt) * p[y0_s:y1_s, x0_s:x1_s]
            w_sum += wt
        along /= np.float32(w_sum)
        resp = np.float32(aw) * np.maximum(along - np.float32(0.20) * p_broad, np.float32(0.0))
        np.maximum(best_line, resp, out=best_line)

    comb_fp = (0.62 * p[foot] + 0.38 * best_line[foot]).astype(np.float32)

    # Inject blind hydrothermal + potential-field coupling corridor prior (H-SASS2-2 de-biasing scarp-only catalogue)
    if hydro_geophys_prior_fp is not None:
        hg_u = _tail_exponential_score(hydro_geophys_prior_fp)
        comb_u = _tail_exponential_score(comb_fp)
        fused_u = 0.78 * comb_u + 0.22 * hg_u + 0.10 * np.sqrt(np.maximum(comb_u - 1.2, 0.0) * np.maximum(hg_u - 1.2, 0.0))
        comb_fp = (1.0 - np.exp(-np.clip(fused_u * 0.35, 0.0, 6.0))).astype(np.float32)

    high_crest = np.maximum(ridge_convex_fp - np.float32(0.9), np.float32(0.0)) * np.clip(
        (hanvf_fp - np.float32(0.5)) / np.float32(1.4), np.float32(0.0), np.float32(1.5)
    )
    crest_pen = np.exp(-0.22 * high_crest)
    road_mod = np.float32(0.84) + np.float32(0.16) * np.clip((road_safe_fp + np.float32(2.0)) / np.float32(3.0), np.float32(0.0), np.float32(1.0))
    piedmont_zone = np.exp(-0.5 * ((hanvf_fp - np.float32(0.10)) / np.float32(1.15)) ** 2)
    pied_mod = np.float32(0.90) + np.float32(0.18) * piedmont_zone

    sharp_fp = comb_fp * crest_pen * road_mod * pied_mod
    mean_s = max(float(sharp_fp.mean()), 1e-8)
    sharp_fp = np.clip(sharp_fp * np.float32(pi_target / mean_s), np.float32(0.0), np.float32(0.95))

    out_2d = np.zeros((H, W), dtype=np.float32)
    out_2d[foot] = sharp_fp
    return out_2d


def allocate_submodular_dots(
    prob_2d: np.ndarray,
    foot: np.ndarray,
    masked_catalogue_2d: np.ndarray,
    collar_px: float = 2.0,
    target_dots: int = 37_654,
    min_spacing_px: float = 2.8,
) -> np.ndarray:
    """Kernel-matched d >= 2.8 px (280 m) greedy 300 m expected-coverage allocator outside B=collar_px.

    Ranks candidates by exact 300 m triangular Tversky kernel integral ``emit.expected_credit(prob_2d)``
    multiplied by centerline sharpness ``(prob_2d)^0.35``, then selects up to ``target_dots`` discrete
    unit-weight peaks separated by ``> min_spacing_px`` so adjacent dots never waste alpha=0.2 FP budget
    on self-overlapping 300 m supremum kernels.
    """
    from gems57 import emit

    H, W = prob_2d.shape
    p_clean = np.where(foot, np.maximum(prob_2d, 0.0), 0.0).astype(np.float32)
    ek = emit.expected_credit(p_clean)
    # Blend kernel integral with local pixel peak to snap dot onto exact scarp centerline
    score_2d = ek * (np.power(p_clean + np.float32(1e-6), np.float32(0.35)))
    del ek, p_clean

    if collar_px > 0.0 and masked_catalogue_2d.any():
        d_cat = ndi.distance_transform_edt(~masked_catalogue_2d)
        allowed = foot & (d_cat > collar_px)
        del d_cat
    else:
        allowed = foot.copy()

    ys, xs = np.nonzero(allowed)
    vals = score_2d[ys, xs]
    del score_2d, allowed

    # Pre-filter to top 550k candidates before sorting for speed (<0.4s)
    cap = min(len(vals), max(target_dots * 14, 550_000))
    if len(vals) > cap:
        part_idx = np.argpartition(-vals, cap - 1)[:cap]
        ys, xs, vals = ys[part_idx], xs[part_idx], vals[part_idx]
    order = np.argsort(-vals, kind="mergesort")
    ys, xs = ys[order], xs[order]
    del vals, order

    r_int = int(np.floor(min_spacing_px))
    dy_off, dx_off = np.mgrid[-r_int : r_int + 1, -r_int : r_int + 1]
    disk_mask = (dy_off * dy_off + dx_off * dx_off) <= (min_spacing_px * min_spacing_px - 1e-6)
    d_oy, d_ox = np.nonzero(disk_mask)
    d_oy = (d_oy - r_int).astype(np.int32)
    d_ox = (d_ox - r_int).astype(np.int32)

    # Pad blocked array by r_int so inner loop needs ZERO boundary checks!
    pad = r_int
    blocked = np.zeros((H + 2 * pad, W + 2 * pad), dtype=bool)
    out = np.zeros((H, W), dtype=np.float32)
    ys_p = ys + pad
    xs_p = xs + pad

    n_emitted = 0
    for yp, xp in zip(ys_p.tolist(), xs_p.tolist()):
        if blocked[yp, xp]:
            continue
        out[yp - pad, xp - pad] = 1.0
        blocked[yp + d_oy, xp + d_ox] = True
        n_emitted += 1
        if n_emitted >= target_dots:
            break

    return out
