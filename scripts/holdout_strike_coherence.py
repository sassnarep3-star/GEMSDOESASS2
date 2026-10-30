#!/usr/bin/env python3
"""Experiment 2 of 3 — strike-coherence echelon corridor (hypothesis H-S1), buffered holdout.

Hypothesis H-S1 (ranked #1 of the candidate list in research/2026-10-30-hypotheses.md):
  Basin-and-Range normal faults are organised into sub-parallel, en-echelon arrays. Where
  mapped (visible) fault traces share a regional strike, an unmapped fault of the same
  array is expected 1–4 km (10–40 px) off the nearest mapped trace, not on it.

Layer: USGS/INGENIOUS catalogue geometry ONLY (visible faults after the 10 px buffer).
Signature targeted: regional strike coherence R(x) of visible traces (structure tensor,
  sigma 6 px locally, pooled over sigma 30 px) multiplied by an off-trace band exp(-((d-25)/10)^2),
  d = distance to the nearest visible trace.
Non-fault mimic named in advance: parallel drainage/erosional scarps and piedmont-slope
  breaks that align with the same regional stress field. The catalogue cannot separate them.
Difference from the implemented generator: the generator uses a distance-only gamma term
  times a seeded random field; H-S1 uses orientation coherence and a band, and has no random term.

Evaluation identical to scripts/holdout_proxy_experiment.py (shared src/gems/metric.py,
same folds, same 10 px buffer, same masking, same placement budget 22,163 dots).
Output: evidence/holdout_strike_coherence.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.metric import bootstrap_dti, dti_binary, per_component_terms  # noqa: E402

_spec = importlib.util.spec_from_file_location("hpe", ROOT / "scripts" / "holdout_proxy_experiment.py")
hpe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hpe)
gen = hpe.gen

BUFFER = 10.0
SPARSE_BUDGET = 22163
OUT = ROOT / "evidence" / "holdout_strike_coherence.json"


def strike_coherence(visible: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Regional strike coherence R(x) in [0,1] of the visible trace network."""
    v = gaussian_filter(visible.astype(np.float64), sigma=2.0)
    gy, gx = np.gradient(v)
    jxx = gaussian_filter(gx * gx, 6.0)
    jyy = gaussian_filter(gy * gy, 6.0)
    jxy = gaussian_filter(gx * gy, 6.0)
    # line orientation is perpendicular to the gradient: doubled-angle vector of the trace direction
    c2 = (jyy - jxx)
    s2 = -2.0 * jxy
    mag = np.sqrt(c2 * c2 + s2 * s2)
    denom = jxx + jyy + 1e-12
    local_coh = mag / denom  # 0 isotropic .. 1 perfectly linear
    weight = local_coh * (jxx + jyy)  # trace-strength weight
    zr = gaussian_filter(weight * c2 / (mag + 1e-12), 30.0)
    zi = gaussian_filter(weight * s2 / (mag + 1e-12), 30.0)
    wsum = gaussian_filter(weight, 30.0) + 1e-12
    R = np.sqrt(zr * zr + zi * zi) / wsum
    R = np.clip(R, 0.0, 1.0)
    R[~foot] = 0.0
    return R.astype(np.float32)


def h_s1_propensity(visible: np.ndarray, foot: np.ndarray) -> np.ndarray:
    d = distance_transform_edt(~visible).astype(np.float32)
    band = np.exp(-(((d - 25.0) / 10.0) ** 2))
    R = strike_coherence(visible, foot)
    prop = R * band
    prop[visible] = 0.0
    prop[~foot] = 0.0
    return hpe.rescale_in_footprint(prop, foot)


def main() -> int:
    foot, cat_all = gen.load_grid()
    lab, n_seg = label(cat_all, structure=np.ones((3, 3), dtype=int))
    seg_fold = hpe.fold_assignment(lab, n_seg)
    names = ["H_S1_strike_coherence", "A_sparse_blind", "C_random_null"]
    pooled = {nm: dict(T_c=0, G_c=0, M_c=0, n_pred=0) for nm in names}
    sums = {nm: dict(TP=0.0, FP=0.0, FN=0.0, dots=0) for nm in names}
    ids_all: list[int] = []
    folds_out = []
    for k in range(hpe.N_FOLDS):
        held_mask = (seg_fold == k) & cat_all
        if held_mask.sum() == 0:
            continue
        ids_all.extend(int(s) for s in np.unique(lab[held_mask]))
        d_held = distance_transform_edt(~held_mask)
        visible = cat_all & ~held_mask & (d_held > BUFFER)
        masked = cat_all & ~held_mask
        truth = held_mask & foot
        score_mask = ~masked & foot

        prop_h = h_s1_propensity(visible, foot)
        gen.MAX_DOTS = SPARSE_BUDGET
        dots_h = gen.place_dots(prop_h, foot, visible) > 0.5
        prop_a = gen.build_propensity(foot, visible)
        dots_a = gen.place_dots(prop_a, foot, visible) > 0.5
        rng = np.random.default_rng(20261031 + k)  # identical seed to the primary experiment
        pc = rng.uniform(size=foot.shape).astype(np.float32)
        pc[~foot] = 0.0
        dots_c = gen.place_dots(pc, foot, visible) > 0.5

        rec = {"fold": k, "withheld_truth_pixels": int(truth.sum()), "arms": {}}
        for nm, dots in [(names[0], dots_h), (names[1], dots_a), (names[2], dots_c)]:
            pred = dots & score_mask
            res = dti_binary(pred, truth, score_mask=score_mask)
            terms = per_component_terms(pred, truth, lab, n_seg)
            for key in ("T_c", "G_c", "M_c"):
                pooled[nm][key] = pooled[nm][key] + terms[key]
            pooled[nm]["n_pred"] += terms["n_pred"]
            sums[nm]["TP"] += res["T"]
            sums[nm]["FP"] += res["FP"]
            sums[nm]["FN"] += res["FN"]
            sums[nm]["dots"] += res["n_pred"]
            rec["arms"][nm] = {"DTI": res["dti"], "TP_w": res["T"], "FP_w": res["FP"], "FN_w": res["FN"],
                               "dots_scored": res["n_pred"]}
        bg = np.where((foot & ~masked & ~truth).ravel())[0]
        pick = np.random.default_rng(7).choice(bg, size=min(200_000, bg.size), replace=False)
        neg = np.zeros(foot.size, dtype=bool)
        neg[pick] = True
        neg = neg.reshape(foot.shape)
        auc_h = hpe.auc_of(prop_h.astype(np.float64), truth, neg)
        rec["leakage_canary_auc"] = {"H_S1_propensity_alone": auc_h, "threshold": 0.90,
                                     "leakage_flag": bool(auc_h > 0.90)}
        folds_out.append(rec)
        print(f"[fold {k}] truth={rec['withheld_truth_pixels']} " +
              " ".join(f"{nm}={rec['arms'][nm]['DTI']:.5f}" for nm in names) +
              f" AUC_H_S1={auc_h:.3f}", file=sys.stderr)

    ids = np.array(sorted(set(ids_all)))
    summary = {}
    for nm in names:
        s = sums[nm]
        pooled_dti = s["TP"] / (s["TP"] + 0.2 * s["FP"] + 0.8 * s["FN"]) if s["TP"] > 0 else 0.0
        boot = bootstrap_dti(pooled[nm], ids, n_boot=1000, seed=20261030)
        summary[nm] = {"pooled_DTI": float(pooled_dti),
                       "ci95_cluster_bootstrap_over_withheld_segments": [boot["lo"], boot["hi"]],
                       "TP_w": s["TP"], "FP_w": s["FP"], "FN_w": s["FN"], "dots_scored": s["dots"]}
    out = {
        "label": "HOLDOUT-DTI (PROXY TRUTH: withheld USGS/INGENIOUS fault segments; NOT an organizer score)",
        "hypothesis": "H-S1 strike-coherence echelon corridor (see module docstring)",
        "evaluator": "src/gems/metric.py dti_binary + per_component_terms + bootstrap_dti",
        "buffer_px": BUFFER,
        "withheld_positives_total": int(sum(f["withheld_truth_pixels"] for f in folds_out)),
        "withheld_segments_total": len(ids),
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summary,
        "folds": folds_out,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: {"pooled_DTI": round(v["pooled_DTI"], 5),
                          "ci95": [round(x, 5) for x in v["ci95_cluster_bootstrap_over_withheld_segments"]]}
                      for k, v in summary.items()}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
