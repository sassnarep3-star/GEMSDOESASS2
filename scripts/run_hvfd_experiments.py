#!/usr/bin/env python3
"""Execute Gate-1 Leakage Canary + Pre-Registered Experiments EXP-1, EXP-2, EXP-3 + Uniqueness & Packaging.

Strict Parallel-Run Protocol enforcement:
  - Budget: Exactly 3 experiments (EXP-1, EXP-2, EXP-3).
  - Gate 1: Single-feature ROC-AUC <= 0.90 across all 48 static + 6 fold-mechanical features (54 total).
  - Gate 2: Exact pooled hide-and-recover HOLDOUT-DTI (`gems57-pooled-hide-v2`, N=11,321, 1,000-draw
    20 km spatial block bootstrap 95% CI) + zero-context blind quadrant HOLDOUT-DTI (`spatial.folds`,
    buffer_px=80, N=60,988).
  - Gate 3: Pre-placement continuous |Spearman| <= 0.90 AND post-placement discrete 3-px dot overlap <= 0.70
    across all accessible focus-site & historical registry rasters.
  - Gate 4: Zero-intervention format/range validation via `vendor/gems57/submission_writer.py` & `validate.py`.
"""
from __future__ import annotations

import gc
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
try:
    CURRENT_BRANCH = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
    ).strip() or "detached"
except (OSError, subprocess.SubprocessError):
    CURRENT_BRANCH = "unknown"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from gems57 import evaluate_holdout as eh
from gems57 import holdout as h57
from gems57 import spatial as sp57
from gems57 import submission_writer as sw57
from gems57 import validate as v57
from gems57.grid import load_grid

from gems_sass2.audit import audit_candidate_uniqueness, discover_registry_tifs
from gems_sass2.features import (
    ALL_FEATURE_NAMES,
    STATIC_FEATURE_NAMES,
    build_static_feature_memmap,
    extract_visible_mechanics,
)
from gems_sass2.models import (
    _make_hgbt,
    _predict_proba_chunked,
    allocate_submodular_dots,
    bayes_prior_calibrate,
    fit_predict_loqo_experts,
    fuse_dual_population,
    oriented_collinearity_sharpen,
    run_single_feature_canary,
)


def _eval_pooled_terms(pred_2d: np.ndarray, folds: list[dict], foot: np.ndarray) -> np.ndarray:
    acc = None
    for f in folds:
        _, terms = eh.evaluate(pred_2d, f, foot)
        acc = terms if acc is None else (acc + terms)
    return acc


def _hydro_composite_from_mm(mm: np.memmap) -> np.ndarray:
    # Combine thermal wells/springs, geothermometers, 2m probes, paleo sinter, demag trough & vent bridge
    cols = (13, 14, 15, 16, 21, 22)
    acc = np.zeros(mm.shape[0], dtype=np.float32)
    for c in cols:
        acc += np.maximum(np.asarray(mm[:, c], dtype=np.float32), np.float32(0.0))
    return acc / np.float32(len(cols))


def _fit_blind_quadrant_oof(
    static_mm: np.memmap,
    foot: np.ndarray,
    cat: np.ndarray,
    pi_target: float = 0.002507,
    seed: int = 20261027,
) -> tuple[np.ndarray, list[dict]]:
    """Evaluate zero-context blind spatial quadrants (`spatial.folds`, buffer_px=80, N=60,988)."""
    sfolds = list(sp57.folds(cat, foot, buffer_px=80))
    oof_fp = np.zeros(static_mm.shape[0], dtype=np.float32)

    for sf in sfolds:
        q = int(sf["fold"])
        train_2d = sf["train"]
        vis_2d = sf["visible"]
        train_fp = train_2d[foot]
        vis_fp = vis_2d[foot]
        d_vis_fp = ndi.distance_transform_edt(~vis_2d).astype(np.float32)[foot]

        pos_idx = np.flatnonzero(train_fp & vis_fp)
        neg_pool = np.flatnonzero(train_fp & (~vis_fp) & (d_vis_fp > 3.0))
        rng = np.random.default_rng(seed + 700 + q * 31)
        neg_idx = np.sort(rng.choice(neg_pool, size=min(len(neg_pool), len(pos_idx) * 8), replace=False))

        tr_idx = np.concatenate([pos_idx, neg_idx])
        y_tr = np.concatenate([np.ones(len(pos_idx), dtype=np.uint8), np.zeros(len(neg_idx), dtype=np.uint8)])
        pi_train = float(len(pos_idx) / len(tr_idx))

        X_tr = np.asarray(static_mm[tr_idx, :], dtype=np.float32)
        te_fp_mask = sf["region"][foot]
        te_idx = np.flatnonzero(te_fp_mask)

        clf = _make_hgbt(seed + 700 + q)
        clf.fit(X_tr, y_tr)
        del X_tr
        p_raw = _predict_proba_chunked(clf, static_mm, te_idx)
        oof_fp[te_idx] = bayes_prior_calibrate(p_raw, pi_train=pi_train, pi_target=pi_target)
        gc.collect()

    oof_2d = np.zeros(foot.shape, dtype=np.float32)
    oof_2d[foot] = oof_fp
    # For blind quadrants, `visible` inside test quadrant `region` is empty, so masked_known = visible!
    sfolds_eval = []
    for sf in sfolds:
        sf_copy = dict(sf)
        sf_copy["masked_known"] = sf["visible"]
        sfolds_eval.append(sf_copy)
    return oof_2d, sfolds_eval


def main() -> int:
    t_start = time.time()
    data_dir = ROOT / ".cache" / "gems_data"
    feat_cache = ROOT / ".cache" / "sass2_features"
    ev_dir = ROOT / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)

    print("[1/7] Loading verified grid and 48-channel static feature memmap...")
    grid_obj = load_grid(data_dir)
    foot = grid_obj.footprint
    cat = grid_obj.catalogue
    static_mm, _, _, _ = build_static_feature_memmap(data_dir=data_dir, cache_dir=feat_cache, force=False)

    print("[2/7] Building canonical gems57-pooled-hide-v2 holdout split (seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)...")
    folds, quad_2d = h57.buffered_component_draw(grid_obj, seed=20, hide_frac=0.20, buffer_px=3, boundary_px=12)
    visible_holdout = folds[0]["visible"]
    k_withheld = int(sum(int((f["truth"] & foot & f["region"] & ~f["masked_known"]).sum()) for f in folds))
    print(f"      Withheld positives N = {k_withheld:,d}; visible catalogue pixels = {int(visible_holdout.sum()):,d}")

    print("[3/7] Extracting 6 fold-proper cross-component mechanical features from visible_holdout ONLY...")
    hydro_comp_fp = _hydro_composite_from_mm(static_mm)
    mech_holdout_fp = extract_visible_mechanics(visible_holdout, foot, hydro_comp_fp)

    print("[4/7] Running Gate-1 Single-Feature Leakage Canary across all 54 features...")
    canary = run_single_feature_canary(static_mm, mech_holdout_fp, ALL_FEATURE_NAMES, foot, folds, auc_limit=0.90)
    (ev_dir / "leakage_canary.json").write_text(json.dumps(canary, indent=2) + "\n", encoding="utf-8")
    print(f"      Canary passed = {canary['canary_passed']} | max single-feature symmetric AUC = {canary['max_symmetric_auc']:.4f} ({canary['max_auc_feature']}) <= 0.90")
    if not canary["canary_passed"]:
        raise RuntimeError(f"STOP: Gate-1 Leakage Canary failed on {canary['max_auc_feature']} (AUC={canary['max_symmetric_auc']})")

    print("[5/7] Computing holdout baselines (random_37654, single_slope, fair_h33) + running 3 Pre-Registered Experiments (EXP-1, EXP-2, EXP-3)...")
    d_vis_hold = ndi.distance_transform_edt(~visible_holdout).astype(np.float32)

    # Baseline 1: random_37654 outside B=2 collar of visible
    rng_rand = np.random.default_rng(20261027)
    elig_rand = np.flatnonzero(foot & (d_vis_hold > 2.0))
    rand_2d = np.zeros(foot.shape, dtype=np.float32)
    rand_2d.ravel()[rng_rand.choice(elig_rand, size=37_654, replace=False)] = 1.0

    # Baseline 2: single_slope (det_elev_slope calibrated + greedy_allocate)
    slope_z_fp = np.asarray(static_mm[:, 0], dtype=np.float32)
    slope_prob_fp = 1.0 / (1.0 + np.exp(-np.clip(slope_z_fp, -8.0, 8.0)))
    slope_prob_2d = np.zeros(foot.shape, dtype=np.float32)
    slope_prob_2d[foot] = bayes_prior_calibrate(slope_prob_fp, pi_train=0.5, pi_target=0.002507)
    single_slope_2d = allocate_submodular_dots(slope_prob_2d, foot, visible_holdout, collar_px=2.0, target_dots=37_654)
    del slope_prob_2d

    # Baseline 3: fair_h33 (d2.8 pruned by visible > 2 px)
    with rasterio.open(data_dir / "scored" / "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        d28_raw = ds.read(1)
    d28_dots = np.isfinite(d28_raw) & (d28_raw > 0) & foot
    fair_h33_2d = np.where(d28_dots & (d_vis_hold > 2.0), 1.0, 0.0).astype(np.float32)
    del d28_raw, d28_dots, d_vis_hold

    # Train spatial LOQO Expert A & Expert B once on visible_holdout (shared cleanly across EXP-1..3)
    hold_oof_cache = feat_cache / "loqo_holdout_oof_v1.npz"
    if hold_oof_cache.exists():
        z = np.load(hold_oof_cache)
        loqo_res = {"oof_expert_a_fp": z["a"], "oof_expert_b_fp": z["b"], "fold_diagnostics": json.loads(str(z["diag"]))}
    else:
        loqo_res = fit_predict_loqo_experts(
            static_mm=static_mm,
            mech_fp=mech_holdout_fp,
            foot=foot,
            quad_2d=quad_2d,
            visible_2d=visible_holdout,
            deadband_px=12,
            neg_pos_ratio=10,
            pi_target=0.002507,
            seed=20261027,
        )
        np.savez(hold_oof_cache, a=loqo_res["oof_expert_a_fp"], b=loqo_res["oof_expert_b_fp"], diag=json.dumps(loqo_res["fold_diagnostics"]))
    p_a_fp = loqo_res["oof_expert_a_fp"]
    p_b_fp = loqo_res["oof_expert_b_fp"]

    # --- EXP-1: Zero-Catalogue Multi-Sensor Hydrothermal & Piedmont Detector (Expert A: H-SASS2-2 + H-SASS2-3) ---
    t_e1 = time.time()
    prob_exp1_2d = np.zeros(foot.shape, dtype=np.float32)
    prob_exp1_2d[foot] = p_a_fp
    dots_exp1_2d = allocate_submodular_dots(prob_exp1_2d, foot, visible_holdout, collar_px=2.0, target_dots=37_654)
    dt_e1 = round(time.time() - t_e1, 2)
    print(f"      EXP-1 allocated {int((dots_exp1_2d > 0).sum()):,d} dots ({dt_e1:.1f}s)")

    # --- EXP-2: Dual-Population Hydrothermal + Cross-Component Fracture Mechanics Synthesis (HVFD: H-SASS2-1) ---
    t_e2 = time.time()
    p_hvfd_fp = fuse_dual_population(p_a_fp, p_b_fp, w_a=0.74, w_b=0.26, pi_target=0.002507)
    prob_exp2_2d = np.zeros(foot.shape, dtype=np.float32)
    prob_exp2_2d[foot] = p_hvfd_fp
    dots_exp2_2d = allocate_submodular_dots(prob_exp2_2d, foot, visible_holdout, collar_px=2.0, target_dots=37_654)
    dt_e2 = round(time.time() - t_e2, 2)
    print(f"      EXP-2 allocated {int((dots_exp2_2d > 0).sum()):,d} dots ({dt_e2:.1f}s)")

    # --- EXP-3: Oriented 500 m Strike-Collinearity + Blind Hydrothermal/Geophysical Corridor De-biasing (HVFD-HydroCollinear) ---
    t_e3 = time.time()
    hanvf_fp = np.asarray(static_mm[:, 2], dtype=np.float32)
    ridge_fp = np.asarray(static_mm[:, 3], dtype=np.float32)
    road_fp = np.asarray(static_mm[:, 12], dtype=np.float32)
    # Blind hydrothermal + potential-field structural corridor prior (zero scarp-catalogue bias!)
    hg_prior_fp = (
        1.20 * hydro_comp_fp
        + 0.70 * np.maximum(np.asarray(static_mm[:, 31], dtype=np.float32), np.float32(0.0))  # Gallardo-Meju grav x mag
        + 0.65 * np.maximum(np.asarray(static_mm[:, 33], dtype=np.float32), np.float32(0.0))  # Anderson transtension strike
        + 0.55 * np.maximum(np.asarray(static_mm[:, 8], dtype=np.float32), np.float32(0.0))   # 10m fluvial chi knickzone
        + 0.50 * np.maximum(np.asarray(static_mm[:, 18], dtype=np.float32), np.float32(0.0))  # MT conductivity gradient
    ).astype(np.float32)
    prob_exp3_2d = oriented_collinearity_sharpen(prob_exp2_2d, foot, hanvf_fp, ridge_fp, road_fp, hydro_geophys_prior_fp=hg_prior_fp, pi_target=0.002507)
    dots_exp3_2d = allocate_submodular_dots(prob_exp3_2d, foot, visible_holdout, collar_px=2.0, target_dots=37_654, min_spacing_px=3.05)
    dt_e3 = round(time.time() - t_e3, 2)
    print(f"      EXP-3 allocated {int((dots_exp3_2d > 0).sum()):,d} dots ({dt_e3:.1f}s)")

    # Score all arms on gems57-pooled-hide-v2 with 1,000-draw 20 km spatial block bootstrap
    arms_2d = {
        "random_37654": rand_2d,
        "single_slope": single_slope_2d,
        "fair_h33": fair_h33_2d,
        "EXP1_zero_cat_hydro_piedmont": dots_exp1_2d,
        "EXP2_hvfd_dual_population": dots_exp2_2d,
        "EXP3_hvfd_collinear_sharpened": dots_exp3_2d,
    }
    terms_by_arm = {name: _eval_pooled_terms(arr, folds, foot) for name, arr in arms_2d.items()}

    # Determine best experiment among EXP-1, EXP-2, EXP-3
    exp_keys = ("EXP1_zero_cat_hydro_piedmont", "EXP2_hvfd_dual_population", "EXP3_hvfd_collinear_sharpened")
    raw_dtis = {k: float(eh.from_terms(terms_by_arm[k].sum(axis=0))) for k in arms_2d}
    best_exp_key = max(exp_keys, key=lambda k: raw_dtis[k])

    pooled_primary = eh.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate=best_exp_key)
    for k, s in pooled_primary["scores"].items():
        print(f"      PRIMARY [{eh.VERSION}] {k:32s} -> DTI = {s['dti']:.5f}  95% CI [{s['ci95'][0]:.5f}, {s['ci95'][1]:.5f}]")

    # Secondary Evaluation: Zero-Context Blind Spatial Quadrants (spatial.folds, buffer_px=80, N=60,988)
    print("      Evaluating Zero-Context Blind Spatial Quadrants (spatial.folds, buffer_px=80, N=60,988)...")
    blind_cache = feat_cache / "blind_quad_oof_v1.npz"
    if blind_cache.exists():
        zb = np.load(blind_cache)
        blind_oof_raw_2d = np.zeros(foot.shape, dtype=np.float32)
        blind_oof_raw_2d[foot] = zb["oof_fp"]
        sfolds_eval = [dict(sf, masked_known=sf["visible"]) for sf in sp57.folds(cat, foot, buffer_px=80)]
    else:
        blind_oof_raw_2d, sfolds_eval = _fit_blind_quadrant_oof(static_mm, foot, cat, pi_target=0.002507, seed=20261027)
        np.savez(blind_cache, oof_fp=blind_oof_raw_2d[foot])
    blind_oof_sharp_2d = oriented_collinearity_sharpen(blind_oof_raw_2d, foot, hanvf_fp, ridge_fp, road_fp, hydro_geophys_prior_fp=hg_prior_fp, pi_target=0.002507)
    empty_cat = np.zeros(foot.shape, dtype=bool)
    blind_exp1_dots = allocate_submodular_dots(blind_oof_raw_2d, foot, empty_cat, collar_px=0.0, target_dots=37_654)
    blind_exp3_dots = allocate_submodular_dots(blind_oof_sharp_2d, foot, empty_cat, collar_px=0.0, target_dots=37_654, min_spacing_px=3.05)
    blind_slope_dots = allocate_submodular_dots(
        np.where(foot, single_slope_2d, 0.0), foot, empty_cat, collar_px=0.0, target_dots=37_654
    )
    # Recompute blind single_slope without visible collar
    slope_full_2d = np.zeros(foot.shape, dtype=np.float32)
    slope_full_2d[foot] = bayes_prior_calibrate(slope_prob_fp, pi_train=0.5, pi_target=0.002507)
    blind_slope_dots = allocate_submodular_dots(slope_full_2d, foot, empty_cat, collar_px=0.0, target_dots=37_654)
    del slope_full_2d

    blind_terms = {
        "random_37654": _eval_pooled_terms(rand_2d, sfolds_eval, foot),
        "single_slope_blind": _eval_pooled_terms(blind_slope_dots, sfolds_eval, foot),
        "EXP1_blind_quadrant": _eval_pooled_terms(blind_exp1_dots, sfolds_eval, foot),
        "EXP3_blind_collinear": _eval_pooled_terms(blind_exp3_dots, sfolds_eval, foot),
    }
    pooled_blind = eh.pooled_summary(blind_terms, draws=1000, seed=520810, candidate="EXP3_blind_collinear")
    for k, s in pooled_blind["scores"].items():
        print(f"      BLIND-8KM [spatial.folds N={s['withheld_positive_pixels']}] {k:24s} -> DTI = {s['dti']:.5f}  95% CI [{s['ci95'][0]:.5f}, {s['ci95'][1]:.5f}]")

    del rand_2d, single_slope_2d, fair_h33_2d, prob_exp1_2d, prob_exp2_2d, prob_exp3_2d
    del dots_exp1_2d, dots_exp2_2d, dots_exp3_2d, blind_oof_raw_2d, blind_oof_sharp_2d, mech_holdout_fp
    gc.collect()

    best_score = pooled_primary["scores"][best_exp_key]["dti"]
    fair_h33_score = pooled_primary["scores"]["fair_h33"]["dti"]
    beats_holdout_best = bool(best_score > fair_h33_score)
    delta_vs_h33 = pooled_primary["paired_differences"]["fair_h33"]
    print(f"      Best candidate = {best_exp_key}: HOLDOUT-DTI = {best_score:.5f} vs fair_h33 = {fair_h33_score:.5f} (delta = {delta_vs_h33['delta']:+.5f}, 95% CI {delta_vs_h33['ci95']})")

    print("[6/7] Fitting full-catalogue spatial LOQO inference (`visible = existing_faults.tif`, 2.4 km boundary separation)...")
    full_oof_cache = feat_cache / "loqo_full_oof_v1.npz"
    if full_oof_cache.exists():
        zf = np.load(full_oof_cache)
        full_loqo = {"oof_expert_a_fp": zf["a"], "oof_expert_b_fp": zf["b"], "fold_diagnostics": json.loads(str(zf["diag"]))}
    else:
        mech_full_fp = extract_visible_mechanics(cat, foot, hydro_comp_fp)
        full_loqo = fit_predict_loqo_experts(
            static_mm=static_mm,
            mech_fp=mech_full_fp,
            foot=foot,
            quad_2d=quad_2d,
            visible_2d=cat,
            deadband_px=12,
            neg_pos_ratio=10,
            pi_target=0.002507,
            seed=20261027,
        )
        np.savez(full_oof_cache, a=full_loqo["oof_expert_a_fp"], b=full_loqo["oof_expert_b_fp"], diag=json.dumps(full_loqo["fold_diagnostics"]))
    # Select the highest-DTI experiment that ALSO passes all Parallel-Run Protocol uniqueness gates!
    reg_entries, total_tif_files = discover_registry_tifs([Path("/tmp/gems_ref"), data_dir / "scored"])
    full_cont_by_exp = {}
    f_exp1 = np.zeros(foot.shape, dtype=np.float32)
    f_exp1[foot] = full_loqo["oof_expert_a_fp"]
    full_cont_by_exp["EXP1_zero_cat_hydro_piedmont"] = f_exp1

    f_exp2 = np.zeros(foot.shape, dtype=np.float32)
    f_exp2[foot] = fuse_dual_population(full_loqo["oof_expert_a_fp"], full_loqo["oof_expert_b_fp"], w_a=0.74, w_b=0.26, pi_target=0.002507)
    full_cont_by_exp["EXP2_hvfd_dual_population"] = f_exp2

    full_cont_by_exp["EXP3_hvfd_collinear_sharpened"] = oriented_collinearity_sharpen(
        f_exp2, foot, hanvf_fp, ridge_fp, road_fp, hydro_geophys_prior_fp=hg_prior_fp, pi_target=0.002507
    )

    # Evaluate uniqueness in descending holdout-DTI order so any duplicate arm is logged & stopped per Rule 1,
    # while promoting the highest-DTI arm that beats fair_h33 AND clears all uniqueness gates!
    ranked_exps = sorted(exp_keys, key=lambda k: raw_dtis[k], reverse=True)
    uniq = None
    cont_full_2d = None
    final_pred_2d = None
    uniqueness_by_exp = {}
    for cand_key in ranked_exps:
        c_cont = full_cont_by_exp[cand_key]
        sp_px = 3.05 if cand_key == "EXP3_hvfd_collinear_sharpened" else 2.8
        c_pred = allocate_submodular_dots(c_cont, foot, cat, collar_px=2.0, target_dots=37_654, min_spacing_px=sp_px)
        c_uniq = audit_candidate_uniqueness(c_cont, c_pred, foot, reg_entries)
        uniqueness_by_exp[cand_key] = {
            "holdout_dti": round(raw_dtis[cand_key], 5),
            "beats_fair_h33": bool(raw_dtis[cand_key] > fair_h33_score),
            "max_pre_spearman": c_uniq["worst_pre_placement_spearman"]["pre_placement_spearman"],
            "max_discrete_3px_overlap": c_uniq["worst_discrete_3px_overlap"]["forward_3px_overlap"],
            "max_discrete_3px_file": c_uniq["worst_discrete_3px_overlap"]["name"],
            "all_uniqueness_gates_passed": c_uniq["all_uniqueness_gates_passed"],
        }
        print(
            f"      Uniqueness check [{cand_key}]: DTI={raw_dtis[cand_key]:.5f}, "
            f"max_3px={c_uniq['worst_discrete_3px_overlap']['forward_3px_overlap']*100:.2f}% vs {c_uniq['worst_discrete_3px_overlap']['name']}, "
            f"passed={c_uniq['all_uniqueness_gates_passed']}"
        )
        if uniq is None and c_uniq["all_uniqueness_gates_passed"] and raw_dtis[cand_key] > fair_h33_score:
            best_exp_key = cand_key
            pooled_primary = eh.pooled_summary(terms_by_arm, draws=1000, seed=520810, candidate=best_exp_key)
            best_score = pooled_primary["scores"][best_exp_key]["dti"]
            delta_vs_h33 = pooled_primary["paired_differences"]["fair_h33"]
            cont_full_2d = c_cont
            final_pred_2d = c_pred
            uniq = c_uniq

    if uniq is None:
        raise RuntimeError("STOP: No experiment both beat fair_h33 and passed all Parallel-Run Protocol Rule 1 uniqueness gates!")

    n_final_dots = int((final_pred_2d > 0).sum())
    d_cat_full = ndi.distance_transform_edt(~cat).astype(np.float32)
    dot_d = d_cat_full[final_pred_2d > 0]
    slope_raw_z = np.asarray(static_mm[:, 0], dtype=np.float32)[final_pred_2d[foot] > 0]
    anatomy = {
        "emitted_dots": n_final_dots,
        "min_dist_to_existing_fault_px": round(float(dot_d.min()), 3),
        "frac_d_cat_le_10px": round(float((dot_d <= 10.0).mean()), 4),
        "frac_d_cat_10_to_20px": round(float(((dot_d > 10.0) & (dot_d <= 20.0)).mean()), 4),
        "frac_d_cat_gt_20px": round(float((dot_d > 20.0).mean()), 4),
        "median_d_cat_px": round(float(np.median(dot_d)), 2),
        "frac_moderate_piedmont_slope_z": round(float(((slope_raw_z >= -0.45) & (slope_raw_z <= 1.35)).mean()), 4),
    }
    print(f"      Promoted {best_exp_key} anatomy: {anatomy}")

    uniq["total_registry_tif_files_scanned"] = total_tif_files
    uniq["per_experiment_gate_summary"] = uniqueness_by_exp
    (ev_dir / "uniqueness_audit.json").write_text(json.dumps(uniq, indent=2) + "\n", encoding="utf-8")

    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
    for old_f in dl_dir.glob("gemsdoesass2-hvfd-*"):
        old_f.unlink()

    mask_digest8 = hashlib.sha256(np.packbits((final_pred_2d > 0).ravel()).tobytes()).hexdigest()[:8]
    ts_tag = "20261027T120000Z"
    arm_slug = {
        "EXP1_zero_cat_hydro_piedmont": "hvfd-exp1-zerocat",
        "EXP2_hvfd_dual_population": "hvfd-exp2-dualpop",
        "EXP3_hvfd_collinear_sharpened": "hvfd-exp3-hydrocollinear",
    }[best_exp_key]
    sub_filename = f"gemsdoesass2-{arm_slug}-{n_final_dots}-{ts_tag}-{mask_digest8}-zeros.tif"
    sub_path = dl_dir / sub_filename

    sub_name = f"GEMSDOESASS2-{arm_slug.upper()}-{n_final_dots}-{mask_digest8}"
    sub_note = (
        f"GEMSDOESASS2 {arm_slug} LOQO B=2 {n_final_dots}px "
        f"HOLDOUT-DTI={best_score:.4f} blind8km={pooled_blind['scores']['EXP3_blind_collinear']['dti']:.4f} "
        f"max3pxOv={uniq['worst_discrete_3px_overlap']['forward_3px_overlap']*100:.1f}%"
    )
    assert len(sub_note) <= 140, f"Note exceeds 140 chars: {len(sub_note)}"

    receipt = sw57.write_submission(
        path=sub_path,
        prediction=final_pred_2d,
        sample=data_dir / "sample_submission.tif",
        footprint=foot,
        catalogue=cat,
        name=sub_name,
        note=sub_note,
        metadata={
            "selected_experiment": best_exp_key,
            "holdout_evaluator": eh.VERSION,
            "holdout_dti": round(best_score, 5),
            "holdout_ci95": [round(x, 5) for x in pooled_primary["scores"][best_exp_key]["ci95"]],
            "anatomy": anatomy,
        },
    )
    # Re-verify written GeoTIFF independently via validate.py
    val_check = v57.validate(sub_path, foot, cat)
    v57.assert_submittable(val_check)

    total_elapsed = round(time.time() - t_start, 2)
    exp_summary = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "elapsed_sec": total_elapsed,
        "experiments_budget_max": 3,
        "experiments_executed": 3,
        "primary_holdout_buffered_loqo": pooled_primary,
        "secondary_holdout_blind_quadrants_8km": pooled_blind,
        "loqo_fold_aucs_holdout": loqo_res["fold_diagnostics"],
        "loqo_fold_aucs_full": full_loqo["fold_diagnostics"],
        "selected_experiment": best_exp_key,
        "beats_fair_h33_holdout_best": beats_holdout_best,
        "final_anatomy": anatomy,
    }
    (ev_dir / "hvfd_experiments.json").write_text(json.dumps(exp_summary, indent=2) + "\n", encoding="utf-8")

    verdict = "promote" if (beats_holdout_best and uniq["all_uniqueness_gates_passed"] and val_check["all_checks_passed"] and canary["canary_passed"]) else "negative"
    ps_best = pooled_primary["scores"][best_exp_key]
    ps_blind = pooled_blind["scores"]["EXP3_blind_collinear"]

    run_card = {
        "protocol_version": "GEMSDOESASS2-PARALLEL-RUN-v2.0",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": "sassnarep3-star/GEMSDOESASS2",
        "branch": CURRENT_BRANCH,
        "experiments_used": 3,
        "experiments_budget_max": 3,
        "runtime_seconds": total_elapsed,
        "hypothesis_id": "H-SASS2-1 (incorporating H-SASS2-2 & H-SASS2-3)",
        "hypothesis": (
            "Hydrothermal Vent-Fault Coupled Dual-Population Synthesis (HVFD-HydroCollinear): fusing a 48-channel "
            "zero-catalogue hydrothermal/piedmont/potential-field multi-scale spatial pyramid LOQO detector (Expert A) "
            "with an exact bit-plane leave-self-component-out fracture-tip, dilational wing-crack, en-echelon "
            "relay-bridge, and orphan-vent LOQO detector (Expert B), sharpened by a 500 m 8-azimuth line-integral "
            "strike-collinearity + hydrothermal/geophysical corridor prior and exact R=300 m (3.05 px) kernel-spaced "
            "allocation outside the B=2 px zero-credit catalogue collar."
        ),
        "mechanism": (
            "Permeable unmapped Quaternary/active geothermal faults express via two complementary physical regimes: "
            "(1) blind range-front/intrabasin upflow corridors exhibiting magnetite-destruction demagnetization troughs "
            "(TMI_up150 - RTP_HP on gravity edges), K/Th metasomatism, MT shallow clay-cap gradients, GDR thermal "
            "springs/geothermometers/2m-probes/paleo-sinter mounds, and piedmont break-in-slope + fluvial chi-knickzones; "
            "and (2) off-catalogue along-strike crack-tip propagation lobes and multi-component relay step-overs."
        ),
        "named_non_fault_process_mimic": (
            "Convex erosional mountain ridge crests (-Laplacian(det_elev) at high Height-Above-Basin-Floor), "
            "highway/railroad cut-and-fill embankments (US Census TIGER/Line road prisms), felsic volcanic tuffs, "
            "and non-tectonic evaporitic playa brines."
        ),
        "leakage_canary": {
            "n_features_tested": canary["n_features_tested"],
            "auc_limit": 0.90,
            "max_single_feature_symmetric_auc": canary["max_symmetric_auc"],
            "max_auc_feature": canary["max_auc_feature"],
            "dist_known_fault_px_stripped": True,
            "passed": canary["canary_passed"],
        },
        "holdout_dti": {
            "primary_label": (
                f"HOLDOUT-DTI ({eh.VERSION}, N={ps_best['withheld_positive_pixels']}, "
                f"95% CI [{ps_best['ci95'][0]:.5f}, {ps_best['ci95'][1]:.5f}]): {ps_best['dti']:.5f}"
            ),
            "evaluator_version": eh.VERSION,
            "n_withheld_positives": ps_best["withheld_positive_pixels"],
            "dti": round(ps_best["dti"], 5),
            "ci95": [round(ps_best["ci95"][0], 5), round(ps_best["ci95"][1], 5)],
            "comparators": {
                k: {
                    "dti": round(v["dti"], 5),
                    "ci95": [round(v["ci95"][0], 5), round(v["ci95"][1], 5)],
                }
                for k, v in pooled_primary["scores"].items()
                if k != best_exp_key
            },
            "paired_gain_vs_fair_h33": {
                "delta": round(delta_vs_h33["delta"], 5),
                "ci95": [round(delta_vs_h33["ci95"][0], 5), round(delta_vs_h33["ci95"][1], 5)],
            },
            "zero_context_blind_quadrant_8km": {
                "label": (
                    f"HOLDOUT-DTI ({eh.VERSION} on spatial.folds buffer_px=80, N={ps_blind['withheld_positive_pixels']}, "
                    f"95% CI [{ps_blind['ci95'][0]:.5f}, {ps_blind['ci95'][1]:.5f}]): {ps_blind['dti']:.5f}"
                ),
                "dti": round(ps_blind["dti"], 5),
                "ci95": [round(ps_blind["ci95"][0], 5), round(ps_blind["ci95"][1], 5)],
                "single_slope_blind_dti": round(pooled_blind["scores"]["single_slope_blind"]["dti"], 5),
                "random_37654_blind_dti": round(pooled_blind["scores"]["random_37654"]["dti"], 5),
            },
        },
        "correlation_and_overlap_vs_registry": {
            "unique_registry_rasters_checked": uniq["n_unique_registry_rasters_checked"],
            "total_registry_tif_files_scanned": total_tif_files,
            "max_pre_placement_spearman": uniq["worst_pre_placement_spearman"]["pre_placement_spearman"],
            "max_pre_placement_spearman_file": uniq["worst_pre_placement_spearman"]["name"],
            "max_post_placement_spearman": uniq["worst_post_placement_spearman"]["post_placement_spearman"],
            "max_discrete_3px_dot_overlap": uniq["worst_discrete_3px_overlap"]["forward_3px_overlap"],
            "max_discrete_3px_overlap_file": uniq["worst_discrete_3px_overlap"]["name"],
            "max_symmetric_3px_overlap_all": uniq["worst_symmetric_3px_overlap_all"]["symmetric_min_3px_overlap"],
            "byte_and_pixel_unique": uniq["gates"]["byte_and_pixel_unique"],
            "all_uniqueness_gates_passed": uniq["all_uniqueness_gates_passed"],
        },
        "raster_filename": sub_filename,
        "raster_path": f"docs/downloads/{sub_filename}",
        "zip_filename": sub_path.with_suffix(".zip").name,
        "raster_sha256": receipt["sha256"],
        "zip_sha256": receipt["zip_sha256"],
        "raster_bytes": receipt["bytes"],
        "emitted_positive_pixels": n_final_dots,
        "validator_output": val_check,
        "submission_name": sub_name,
        "submission_note": sub_note,
        "submission_note_chars": len(sub_note),
        "verdict": verdict,
    }
    (ev_dir / "hvfd_exp3_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    print(f"[DONE] Run card written to {ev_dir / 'hvfd_exp3_run_card.json'} | verdict = {verdict} | elapsed = {total_elapsed:.1f}s")
    print(f"       Deliverable TIF: docs/downloads/{sub_filename} (sha256={receipt['sha256'][:16]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
