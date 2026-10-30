#!/usr/bin/env python3
"""Fit and cross-validate an empirical organizer-score estimator on the measured
GEMSDOE portfolio ledger (evidence/org_ledger_measured.json).

Model family: ordinary least squares on a small, physically interpretable feature
set measured from the submitted bytes only:
  n_dots, share of dots beyond the 1/2/3 px catalogue collar, log10 dots,
  median |delta row| / |delta col| (stripiness), value mass.

Reporting: leave-one-site-out cross-validation. The estimator is a *prior over
organizer scores implied by the observed portfolio*; it is not an organizer score
and never replaces a receipt. Scores in the ledger are USER-REPORTED / UNVERIFIED.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def features(r: dict) -> np.ndarray:
    dots = float(r.get("dots_gt0", 0) or 0)
    mass = float(r.get("value_mass", dots) or dots)
    b0 = float(r.get("dots_beyond_0px_of_catalogue", 0) or 0)
    b1 = float(r.get("dots_beyond_1px_of_catalogue", b0) or 0)
    b2 = float(r.get("dots_beyond_2px_of_catalogue", b0) or 0)
    b3 = float(r.get("dots_beyond_3px_of_catalogue", b0) or 0)
    rows = float(r.get("n_unique_rows", 1) or 1)
    cols = float(r.get("n_unique_cols", 1) or 1)
    return np.array([
        np.log10(max(dots, 1.0)),
        (dots - b2) / max(dots, 1.0),      # fraction within the 2 px collar (pruned mass)
        b2 / max(dots, 1.0),               # off-2px share
        mass / max(dots, 1.0) - 1.0,       # 0 for binary rasters, >0 for soft rasters
        np.log10(max(rows, 1.0)) + np.log10(max(cols, 1.0)),
    ], dtype=np.float64)


NAMES = ["log10_dots", "collar2_prune_share", "off2px_share", "softness", "log_span"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, default=ROOT / "evidence" / "org_ledger_measured.json")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "org_score_estimator.json")
    args = ap.parse_args()

    led = json.loads(args.ledger.read_text())
    rows = [r for r in led["records"] if r.get("status") == "measured"]
    X = np.array([features(r) for r in rows])
    y = np.array([float(r["owner_reported_score"]) for r in rows])
    mu, sd = X.mean(axis=0), X.std(axis=0) + 1e-12
    Xs = (X - mu) / sd
    A = np.hstack([np.ones((len(y), 1)), Xs])

    def fit(A, y, lam=1.0):
        reg = lam * np.eye(A.shape[1]); reg[0, 0] = 0.0
        beta = np.linalg.solve(A.T @ A + reg, A.T @ y)
        return beta

    beta = fit(A, y)
    # leave-one-out cross-validation
    pred_loo = np.empty_like(y)
    for i in range(len(y)):
        keep = np.arange(len(y)) != i
        b = fit(A[keep], y[keep])
        pred_loo[i] = float(A[i] @ b)
    resid = y - pred_loo
    loo_rmse = float(np.sqrt((resid ** 2).mean()))
    loo_mae = float(np.abs(resid).mean())
    r2 = 1.0 - float((resid ** 2).sum()) / float(((y - y.mean()) ** 2).sum())

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "class": "EMPIRICAL-PRIOR (fitted on owner-reported scores; not an organizer receipt)",
        "n_rows": len(y),
        "features": NAMES,
        "standardisation": {"mean": [round(float(v), 6) for v in mu],
                            "std": [round(float(v), 6) for v in sd]},
        "coefficients": {"intercept": round(float(beta[0]), 6),
                         **{n: round(float(v), 6) for n, v in zip(NAMES, beta[1:])}},
        "loo_site_metrics": {"rmse": round(loo_rmse, 5), "mae": round(loo_mae, 5), "r2": round(r2, 4)},
        "prediction_95_band_halfwidth": round(1.96 * loo_rmse, 4),
        "rows": [{"site": r["site"], "stem": r["stem"][:48], "score": float(s),
                  "loo_pred": round(float(p), 4), "resid": round(float(s - p), 4)}
                 for r, s, p in zip(rows, y, pred_loo)],
        "caveats": [
            "Same-dots cohorts span 0.1823-0.2778 organizer scores, so geometry-only features cannot identify a score; the band is wide by construction.",
            "Scores are USER-REPORTED / UNVERIFIED; the fit inherits that uncertainty.",
            "Never report an estimate from this model as a score (protocol rule 3).",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"n={len(y)} LOO RMSE={loo_rmse:.4f} MAE={loo_mae:.4f} R2={r2:.3f} "
          f"95% half-width={1.96*loo_rmse:.4f}")
    print(json.dumps(report["coefficients"], indent=2))
    for r in report["rows"]:
        print(f"{r['site']:>12} score={r['score']:<7} loo_pred={r['loo_pred']:<8} resid={r['resid']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
