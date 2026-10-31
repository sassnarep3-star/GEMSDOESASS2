#!/usr/bin/env python3
"""RMC lane experiment: corridor geometry vs dot geometry, and a fitted score transfer.

Three products, all labelled:

  LEAKAGE CANARY   single-channel AUC of every surface channel against the withheld
                   hide-and-recover truth (protocol rule 4: AUC > 0.90 == leakage).
  INSTRUMENT TABLE pooled HOLDOUT-DTI for every emission variant on BOTH shared
                   instruments, with 256-block 95 % cluster-bootstrap CIs.
  SCORE TRANSFER   one free parameter g (the leaderboard truth size, in pixels) in the
                   official DTI expression, fitted on the twelve hash-pinned registry
                   rasters whose scores are USER-REPORTED, validated by leave-one-out.
                   A transfer estimate is a MODEL ESTIMATE, never a score.

No variant's threshold is chosen on the off-catalogue SGMC instrument; tau is chosen on
the hide-and-recover instrument and SGMC is reported as a held-out check.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    evaluate_hide_and_recover,
    evaluate_sgmc_with_ci,
    load_holdout_context,
)
from gems_sass2.metric import ALPHA, BETA, EPS, kernel  # noqa: E402
from gems_sass2.paths import data_dir  # noqa: E402

CACHE = ROOT / ".cache" / "rmc"
REGISTRY_ROOT = pathlib.Path("/home/user/registry")


def terms(mask: np.ndarray, truth_mask: np.ndarray) -> tuple[float, float]:
    """(TP_w, FP_w) of a binary emission against a binary truth, official definitions."""
    tp = float(kernel(ndi.distance_transform_edt(~mask)[truth_mask]).sum())
    fp = float((1.0 - kernel(ndi.distance_transform_edt(~truth_mask)[mask])).sum())
    return tp, fp


def dti_of(tp: float, fp: float, n_truth: float) -> float:
    fn = max(n_truth - tp, 0.0)
    return float(tp / (tp + ALPHA * fp + BETA * fn + EPS))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evidence/rmc_experiment_20261031.json")
    ap.add_argument("--skip-registry", action="store_true")
    ap.add_argument("--budget", type=int, default=37654, help="dot-budget control count")
    args = ap.parse_args()

    ddir = data_dir()
    ctx = load_holdout_context(ddir)
    foot, labels = ctx.foot, ctx.labels
    d_cat = ndi.distance_transform_edt(~labels)
    surf = np.load(CACHE / "surface.npy")
    chz = np.load(CACHE / "channels.npz")

    # ---------------------------------------------------------------- canary ----
    # Union truth of the withheld segments, restricted to each fold's scored domain.
    union_truth = np.zeros(foot.shape, dtype=bool)
    for cell in ctx.cells:
        sub = np.zeros(foot.shape, dtype=bool)
        sub[cell.bbox][cell.truth_coords] = True
        union_truth |= sub & _expand(cell, foot.shape)
    rng = np.random.default_rng(20261031)
    fp_idx = np.flatnonzero(foot.ravel())
    sample = rng.choice(fp_idx, size=min(600_000, fp_idx.size), replace=False)
    y = union_truth.ravel()[sample]
    canary = {"n_truth_sampled": int(y.sum()), "threshold_alarm": 0.90}
    for name in ("S1_pf_lineament", "S2_scarp", "S3_strain", "S4_seismicity",
                 "S5_conduit", "S6_basement", "A_geothermal"):
        v = chz[name].ravel()[sample].astype(np.float64)
        canary[name] = round(float(roc_auc_score(y, v)), 4) if y.any() and (~y).any() else None
    canary["surface"] = round(float(roc_auc_score(y, surf.ravel()[sample])), 4)
    canary["leakage_flag"] = any((v or 0) > 0.90 for k, v in canary.items() if isinstance(v, float))
    print("[canary]", json.dumps(canary))

    # ------------------------------------------------------------- variants ----
    variants: dict[str, np.ndarray] = {}
    eligible = foot & (d_cat > 2.0)          # B = 2 px collar on the public catalogue
    n_elig = int(eligible.sum())
    for frac in (0.002, 0.005, 0.01, 0.02, 0.04, 0.08, 0.15, 0.25):
        k = max(int(round(frac * n_elig)), 1)
        vals = np.where(eligible, surf, -1.0)
        cut = np.partition(vals.ravel(), vals.size - k)[vals.size - k]
        variants[f"corridor_m{frac:g}"] = eligible & (surf >= cut)
    # dot controls on the *same* surface: isolates emission geometry from surface quality
    for k in (args.budget, 44090):
        vals = np.where(eligible, surf, -1.0)
        cut = np.partition(vals.ravel(), vals.size - k)[vals.size - k]
        dots = eligible & (surf >= cut)
        keep = int(dots.sum())
        if keep > k:                            # ties: keep the highest-scoring ties only
            flat = np.flatnonzero(dots.ravel())
            order = np.argsort(-vals.ravel()[flat])
            sel = np.zeros(dots.size, dtype=bool)
            sel[flat[order[:k]]] = True
            dots = sel.reshape(dots.shape)
        variants[f"dots_n{k}"] = dots
    # corridor dilated 1 px (tests the free-lunch asymmetry of the metric)
    base = variants["corridor_m0.04"]
    variants["corridor_m0.04_dil1"] = ndi.binary_dilation(base, iterations=1) & eligible

    rows = {}
    for name, mask in variants.items():
        n = int(mask.sum())
        if n == 0:
            continue
        hr = evaluate_hide_and_recover(mask, ctx, name=name)
        sg = evaluate_sgmc_with_ci(mask, ctx, name=name)
        tp_s, fp_s = terms(mask, ctx.sgmc_off & foot & ~labels)
        g_s = int(ctx.sgmc_n_truth)
        rows[name] = {
            "emitted_px": n, "coverage_of_footprint": round(n / float(foot.sum()), 6),
            "hide_dti": round(hr["pooled_dti"], 6),
            "hide_ci95": [round(v, 6) for v in hr["ci95_cluster_bootstrap"]],
            "hide_detached_dti": round(hr["detached_600m"]["pooled_dti"], 6),
            "hide_n_withheld": hr["n_withheld_positives"],
            "sgmc_dti": round(sg["sgmc_raw_pooled_dti"], 6),
            "sgmc_ci95": [round(v, 6) for v in sg["sgmc_raw_ci95"]],
            "sgmc_coverage": round(tp_s / g_s, 6),
            "sgmc_TP": round(tp_s, 1), "sgmc_FP": round(fp_s, 1), "sgmc_G": g_s,
            "mean_credit_per_px": round(tp_s / n, 6),
        }
        print(f"[variant] {name:>22} n={n:>7} hide={rows[name]['hide_dti']:.4f} "
              f"sgmc={rows[name]['sgmc_dti']:.4f} cov={rows[name]['sgmc_coverage']:.4f} "
              f"credit/px={rows[name]['mean_credit_per_px']:.4f}")

    # ------------------------------------------------- registry + transfer -----
    reg_rows = []
    if not args.skip_registry:
        man = json.loads((ROOT / "registry/registry_manifest.json").read_text())
        for r in man["rasters"]:
            p = REGISTRY_ROOT / r["path"]
            if not p.is_file():
                continue
            with rasterio.open(p) as ds:
                a = ds.read(1).astype(np.float64)
            mask = np.isfinite(a) & (a > 0) & foot
            n = int(mask.sum())
            if n == 0:
                continue
            tp, fp = terms(mask, ctx.sgmc_off & foot & ~labels)
            reg_rows.append({"site": r["site"], "submission": r["name"], "reported": r.get("owner_reported_score"),
                             "dots": n, "sgmc_TP": round(tp, 1), "sgmc_FP": round(fp, 1),
                             "sgmc_coverage": round(tp / ctx.sgmc_n_truth, 6),
                             "sgmc_dti": round(dti_of(tp, fp, ctx.sgmc_n_truth), 6)})
            print(f"[registry] {r['site']:>11} rep={r.get('owner_reported_score')} n={n:>6} "
                  f"sgmcDTI={reg_rows[-1]['sgmc_dti']:.4f} cov={reg_rows[-1]['sgmc_coverage']:.4f}")

    fit = {"note": "g is the leaderboard-equivalent truth size in pixels; the transfer assumes "
                   "the emission's off-catalogue coverage transfers 1:1 to the hidden truth."}
    anchors = [r for r in reg_rows if r.get("reported")]
    if anchors:
        def sse(g: float) -> float:
            e = 0.0
            for r in anchors:
                T = r["sgmc_TP"] * (g / ctx.sgmc_n_truth)
                F = max(r["dots"] - T, 0.0)
                pred = dti_of(T, F, g)
                e += (np.log(max(pred, 1e-9)) - np.log(r["reported"])) ** 2
            return e
        grid = np.exp(np.linspace(np.log(2000.0), np.log(900_000.0), 240))
        vals = np.array([sse(g) for g in grid])
        best = float(grid[int(np.argmin(vals))])
        fit.update(g_pixels=best, g_km_of_100m_px=best * 0.1, log_rmse=float(np.sqrt(vals.min() / len(anchors))))
        preds = []
        for i, r in enumerate(anchors):
            loo_grid = np.exp(np.linspace(np.log(2000.0), np.log(900_000.0), 240))
            def sse_loo(g: float) -> float:
                e = 0.0
                for j, q in enumerate(anchors):
                    if j == i:
                        continue
                    T = q["sgmc_TP"] * (g / ctx.sgmc_n_truth)
                    e += (np.log(max(dti_of(T, max(q["dots"] - T, 0.0), g), 1e-9)) - np.log(q["reported"])) ** 2
                return e
            gg = float(loo_grid[int(np.argmin([sse_loo(g) for g in loo_grid]))])
            T = r["sgmc_TP"] * (gg / ctx.sgmc_n_truth)
            preds.append(round(dti_of(T, max(r["dots"] - T, 0.0), gg), 4))
        pred = np.array(preds)
        obs = np.array([r["reported"] for r in anchors])
        fit.update(loo_predictions=preds, loo_mae=float(np.abs(pred - obs).mean()),
                   loo_max_abs_error=float(np.abs(pred - obs).max()),
                   loo_spearman=float(spearmanr(obs, pred).correlation),
                   loo_overprediction_fraction=float(np.mean(pred > obs)),
                   n_anchors=len(anchors))
        for r, p in zip(anchors, preds):
            r["transfer_estimate_at_g"] = round(dti_of(r["sgmc_TP"] * (best / ctx.sgmc_n_truth),
                                                        max(r["dots"] - r["sgmc_TP"] * (best / ctx.sgmc_n_truth), 0.0), best), 4)
            r["transfer_loo"] = p
        print(f"[transfer] g={best:.0f} px  LOO MAE={fit['loo_mae']:.4f} "
              f"max err={fit['loo_max_abs_error']:.4f}")
    for name, row in rows.items():
        if "sgmc_TP" in row and fit.get("g_pixels"):
            g = fit["g_pixels"]
            T = row["sgmc_TP"] * (g / ctx.sgmc_n_truth)
            row["transfer_model_estimate"] = round(dti_of(T, max(row["emitted_px"] - T, 0.0), g), 4)

    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "lane": "RMC - Recall-Maximal Corridor emission at the DTI-optimal level set",
        "evidence_classes": {"hide_dti": "HOLDOUT-DTI (hide-and-recover, selection instrument)",
                             "sgmc_dti": "HOLDOUT-DTI (off-catalogue SGMC, held-out check)",
                             "transfer_model_estimate": "MODEL ESTIMATE (not a score)",
                             "reported": "USER-REPORTED / UNVERIFIED"},
        "leakage_canary": canary, "variants": rows,
        "registry_anchors": reg_rows, "score_transfer_fit": fit,
        "collar_b_px": 2.0, "eligibility_px": n_elig,
        "ok_to_submit": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n")
    np.savez_compressed(CACHE / "variants.npz", **{k: v.astype(np.uint8) for k, v in variants.items()})
    print(f"[rmc] wrote {args.out}")
    return 0


def _expand(cell, shape) -> np.ndarray:
    sub = np.zeros(shape, dtype=bool)
    sl = cell.bbox
    sub[sl] = cell.active_sub
    return sub


if __name__ == "__main__":
    raise SystemExit(main())
