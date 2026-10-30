#!/usr/bin/env python3
"""Hide-and-recover HOLDOUT-DTI for the sparse-blind generator (Experiment 1 of 3).

Protocol (project parallel-run rules, REUSE clause):
  * Withhold whole catalogue fault segments by spatial fold, with a BUFFER (default 10 px):
    visible catalogue = the other segments, minus anything within BUFFER px of a held-out segment.
  * Every catalogue-derived feature is computed from the VISIBLE faults only.
  * Known (catalogue) pixels are masked from scoring, as the organizer does for USGS/INGENIOUS
    faults (DrivenData staff, 2026-09-16). Only held-out pixels are truth.
  * Scoring uses the shared evaluator ``src/gems/metric.py`` (dti_binary, per_component_terms,
    bootstrap_dti): k(d)=max(1-d/3,0), alpha 0.2 (FP), beta 0.8 (FN), R=3 px (300 m).
  * Leakage canary: each feature alone must reach AUC well below 0.90 on held-out truth vs.
    unmasked background, or it is leakage until disproved.

Arms (all reuse scripts/generate_unique_submission.py functions):
  A  sparse-blind            : generator as shipped (off-fault gamma x seeded random field), 22,163 dots
  A0 ablation                : same placement with the random field removed, 22,163 dots
  B  dense adjacent          : off-fault term only, 37,654 dots (historical dot budget)
  C  random null             : uniform random propensity, 22,163 dots

Output: evidence/holdout_proxy_sparse_blind[_buffer<N>].json. Numbers are HOLDOUT-DTI on a PROXY
truth (withheld USGS/INGENIOUS segments). They are never organizer scores on new faults.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.metric import bootstrap_dti, dti_binary, per_component_terms  # noqa: E402

spec = importlib.util.spec_from_file_location("gen", ROOT / "scripts" / "generate_unique_submission.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

FOLD_BLOCK = 700  # px; spatial blocks used to assign whole segments to folds
N_FOLDS = 4
DENSE_BUDGET = 37654
SPARSE_BUDGET = 22163


def fold_assignment(lab: np.ndarray, n: int) -> np.ndarray:
    fold_of_seg = np.zeros(n + 1, dtype=int)
    for s in range(1, n + 1):
        ys, xs = np.where(lab == s)
        br, bc = int(np.median(ys)) // FOLD_BLOCK, int(np.median(xs)) // FOLD_BLOCK
        fold_of_seg[s] = (br + 2 * bc) % N_FOLDS  # deterministic spatial fold
    return fold_of_seg[lab]


def auc_of(feature: np.ndarray, pos: np.ndarray, neg: np.ndarray) -> float:
    y = np.concatenate([np.ones(int(pos.sum())), np.zeros(int(neg.sum()))])
    s = np.concatenate([feature[pos], feature[neg]])
    return float(roc_auc_score(y, s))


def random_field(seed: int = 20261028) -> np.ndarray:
    """The generator's 'geothermal prior' term, reproduced exactly so it can be canary-tested alone."""
    rng = np.random.default_rng(seed)
    coarse = rng.standard_normal((gen.HEIGHT // 8 + 2, gen.WIDTH // 8 + 2)).astype(np.float32)
    coarse = np.repeat(np.repeat(coarse, 8, axis=0), 8, axis=1)[: gen.HEIGHT, : gen.WIDTH]
    return gaussian_filter(coarse, sigma=24)


def off_fault_term(visible: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Generator's off-fault term: d * exp(-d/4) with d = distance to VISIBLE faults (k=2, theta=4)."""
    d = distance_transform_edt(~visible).astype(np.float64)
    off = (d ** (2.0 - 1.0)) * np.exp(-d / 4.0)
    off = off / (off.max() + 1e-12)
    off[visible] = 0.0
    off[~foot] = 0.0
    return off


def rescale_in_footprint(x: np.ndarray, foot: np.ndarray) -> np.ndarray:
    p2, p98 = np.percentile(x[foot], [2, 98])
    y = np.clip((x - p2) / (p98 - p2 + 1e-12), 0, 1).astype(np.float32)
    y[~foot] = 0.0
    return y


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--buffer", type=float, default=10.0, help="px buffer around held-out segments (primary = 10)")
    args = ap.parse_args()
    BUFFER = args.buffer
    out_path = ROOT / "evidence" / (
        "holdout_proxy_sparse_blind.json" if BUFFER == 10.0 else f"holdout_proxy_sparse_blind_buffer{int(BUFFER)}.json")

    foot, cat_all = gen.load_grid()
    lab, n_seg = label(cat_all, structure=np.ones((3, 3), dtype=int))  # 8-connected segments
    seg_fold = fold_assignment(lab, n_seg)
    print(f"[folds] catalogue segments={n_seg} pixels={int(cat_all.sum())} buffer_px={BUFFER}", file=sys.stderr)

    rf = random_field()
    rf_full = rf  # canary reference
    names = ["A_sparse_blind", "A0_no_random_field", "B_dense_adjacent", "C_random_null"]
    pooled = {nm: dict(T_c=0, G_c=0, M_c=0, n_pred=0) for nm in names}
    ids_all: list[int] = []
    folds_out = []
    sums = {nm: dict(TP=0.0, FP=0.0, FN=0.0, dots=0) for nm in names}

    for k in range(N_FOLDS):
        held_mask = (seg_fold == k) & cat_all
        if held_mask.sum() == 0:
            continue
        held_ids = sorted(int(s) for s in np.unique(lab[held_mask]))
        ids_all.extend(held_ids)
        d_held = distance_transform_edt(~held_mask)
        visible = cat_all & ~held_mask & (d_held > BUFFER)
        masked = cat_all & ~held_mask          # all known faults except the withheld truth
        truth = held_mask & foot
        score_mask = ~masked & foot

        # generator with VISIBLE faults as its catalogue
        prop_a = gen.build_propensity(foot, visible)
        gen.MAX_DOTS = SPARSE_BUDGET
        dots_a = gen.place_dots(prop_a, foot, visible) > 0.5
        p0 = rescale_in_footprint(off_fault_term(visible, foot), foot)
        dots_a0 = gen.place_dots(p0, foot, visible) > 0.5
        gen.MAX_DOTS = DENSE_BUDGET
        dots_b = gen.place_dots(p0, foot, visible) > 0.5
        rng = np.random.default_rng(20261031 + k)
        pc = rng.uniform(size=foot.shape).astype(np.float32)
        pc[~foot] = 0.0
        gen.MAX_DOTS = SPARSE_BUDGET
        dots_c = gen.place_dots(pc, foot, visible) > 0.5

        rec = {"fold": k, "withheld_segments": len(held_ids), "withheld_truth_pixels": int(truth.sum()),
               "visible_pixels": int(visible.sum()), "arms": {}}
        for nm, dots in [(names[0], dots_a), (names[1], dots_a0), (names[2], dots_b), (names[3], dots_c)]:
            pred = dots & score_mask
            res = dti_binary(pred, truth, score_mask=score_mask)  # shared evaluator
            terms = per_component_terms(pred, truth, lab, n_seg)  # shared evaluator, per-segment terms
            for key in ("T_c", "G_c", "M_c"):
                pooled[nm][key] = pooled[nm][key] + terms[key]
            pooled[nm]["n_pred"] += terms["n_pred"]
            sums[nm]["TP"] += res["T"]
            sums[nm]["FP"] += res["FP"]
            sums[nm]["FN"] += res["FN"]
            sums[nm]["dots"] += res["n_pred"]
            rec["arms"][nm] = {"DTI": res["dti"], "TP_w": res["T"], "FP_w": res["FP"], "FN_w": res["FN"],
                               "dots_scored": res["n_pred"], "dots_total": int(dots.sum())}
        # leakage canary: each feature alone vs. unmasked background (balanced sample, fixed seed)
        bg = np.where((foot & ~masked & ~truth).ravel())[0]
        pick = np.random.default_rng(7).choice(bg, size=min(200_000, bg.size), replace=False)
        neg = np.zeros(foot.size, dtype=bool)
        neg[pick] = True
        neg = neg.reshape(foot.shape)
        auc_off = auc_of(off_fault_term(visible, foot), truth, neg)
        auc_rf = auc_of(rf_full.astype(np.float64), truth, neg)
        rec["leakage_canary_auc"] = {
            "off_fault_term_from_visible_only": auc_off,
            "random_field_term_alone": auc_rf,
            "threshold": 0.90,
            "leakage_flag": bool(max(auc_off, auc_rf) > 0.90),
        }
        folds_out.append(rec)
        print(f"[fold {k}] truth={rec['withheld_truth_pixels']} " +
              " ".join(f"{nm}={rec['arms'][nm]['DTI']:.5f}" for nm in names), file=sys.stderr)

    summary = {}
    ids = np.array(sorted(set(ids_all)))
    for nm in names:
        s = sums[nm]
        pooled_dti = s["TP"] / (s["TP"] + 0.2 * s["FP"] + 0.8 * s["FN"]) if s["TP"] > 0 else 0.0
        boot = bootstrap_dti(pooled[nm], ids, n_boot=1000, seed=20261030)
        summary[nm] = {
            "pooled_DTI": float(pooled_dti),
            "ci95_cluster_bootstrap_over_withheld_segments": [boot["lo"], boot["hi"]],
            "TP_w": s["TP"], "FP_w": s["FP"], "FN_w": s["FN"],
            "dots_scored": s["dots"],
        }
    out = {
        "label": "HOLDOUT-DTI (PROXY TRUTH: withheld USGS/INGENIOUS fault segments; NOT an organizer score)",
        "evaluator": "src/gems/metric.py dti_binary + per_component_terms + bootstrap_dti (official DTI; alpha 0.2, beta 0.8, R 3 px)",
        "evaluator_version": "gems.metric (repo HEAD at run time)",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "buffer_px": BUFFER,
        "n_folds": len(folds_out),
        "withheld_positives_total": int(sum(f["withheld_truth_pixels"] for f in folds_out)),
        "withheld_segments_total": len(ids),
        "masking": "all catalogue pixels except withheld truth are masked from scoring",
        "summary": summary,
        "folds": folds_out,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "generator_sha256": hashlib.sha256((ROOT / "scripts" / "generate_unique_submission.py").read_bytes()).hexdigest(),
    }
    out_path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: {"pooled_DTI": round(v["pooled_DTI"], 5), "ci95": [round(x, 5) for x in v["ci95_cluster_bootstrap_over_withheld_segments"]]}
                      for k, v in summary.items()}, indent=1))
    print(f"wrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
