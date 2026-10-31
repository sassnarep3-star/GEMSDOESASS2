"""Is 250,000 cells the right budget?  Two questions, one script.

Q1. Does the nine-site "density law" hold as a mechanistic model?
    DTI(N) = C / (0.2N + 0.8(G - C))
    Fit C and G to the nine owner-reported scores and print every residual.
    C has a physical reading -- the truth-cell mass the family actually
    recovers -- and G the implied size of the hidden truth.  Both are
    *effective parameters of a fit*, not measurements.

Q2. Given that law, what emission budget maximises the expected score?
    The law is scale-free in G once it is written in terms of
        r = T / |G|        coverage of the hidden truth
        h = T / N          truth mass recovered per predicted cell
    because DTI = r / (0.2 r / h + 0.8 (1 - r)).

    r and h are measurable against a *proxy* truth.  The best proxy in this
    repository is the SGMC fault compilation: 83,593 cells, independent of the
    catalogue the model was trained on.  So we sweep the budget, measure
    (r, h) on both proxies, and read off the implied score at the organiser's
    implied |G|.  A "ribbon" variant (dilate each dot by one pixel) tests the
    metric's own exchange rate: one recovered truth cell is worth up to
    (1 - 0.2 DTI) / (0.2 DTI) ~ 17 wasted cells.

Everything printed here is a MODEL ESTIMATE.  Nothing is an organiser score.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.design import jittered_design  # noqa: E402

# ---------------------------------------------------------------- Q1 the law
NINE = [
    ("GEMSDOE24", 60069, 0.2477),
    ("GEMSDOE25", 44090, 0.2600),
    ("GEMSDOE27", 61328, 0.2449),
    ("GEMSDOE28", 37660, 0.2710),
    ("GEMSDOE30", 44090, 0.2600),
    ("GEMSDOE31", 40199, 0.2708),
    ("GEMSDOE32", 37654, 0.2778),
    ("GEMSDOE33", 41865, 0.2632),
    ("GEMSDOE36", 38854, 0.2750),
]


def law(C: float, G: float, n: float) -> float:
    """DTI for a design that spends n cells and recovers C truth mass."""
    return C / (0.2 * C + 0.2 * (n - C) + 0.8 * (G - C))


def fit_law() -> dict:
    """Grid-search C, G, then polish.  Two parameters, nine observations."""
    best = None
    for C in np.arange(6_000.0, 22_000.0, 50.0):
        for G in np.arange(30_000.0, 120_000.0, 250.0):
            err = sum((law(C, G, n) - s) ** 2 for _, n, s in NINE)
            if best is None or err < best[0]:
                best = (err, C, G)
    _, C, G = best
    for _ in range(6):  # coordinate polish
        step_c, step_g = 50.0, 250.0
        for _ in range(40):
            improved = False
            for dC, dG in ((step_c, 0), (-step_c, 0), (0, step_g), (0, -step_g)):
                err = sum((law(C + dC, G + dG, n) - s) ** 2 for _, n, s in NINE)
                if err < best[0]:
                    best = (err, C + dC, G + dG)
                    C, G = C + dC, G + dG
                    improved = True
            if not improved:
                step_c /= 2.0
                step_g /= 2.0
        break
    rows = []
    ss_tot = sum((s - np.mean([x[2] for x in NINE])) ** 2 for _, _, s in NINE)
    for site, n, s in NINE:
        pred = law(C, G, n)
        rows.append(dict(site=site, n=n, reported=s, law=round(pred, 4),
                         residual=round(pred - s, 4)))
    ss_res = sum(r["residual"] ** 2 for r in rows)
    return dict(C_recovered_truth_cells=round(C, 1), G_implied_hidden_cells=round(G, 1),
                r_squared=round(1.0 - ss_res / ss_tot, 4),
                rms_residual=round(float(np.sqrt(ss_res / len(rows))), 4),
                max_abs_residual=round(max(abs(r["residual"]) for r in rows), 4),
                coverage_r=round(C / G, 4), rows=rows)


# ------------------------------------------------------------ Q2 the sweep
def main() -> int:
    out = {"scope": "MODEL ESTIMATE, never an organiser score", "law": fit_law()}
    print(f"law: C={out['law']['C_recovered_truth_cells']:,.0f} "
          f"G={out['law']['G_implied_hidden_cells']:,.0f} "
          f"R2={out['law']['r_squared']:.4f} "
          f"max|res|={out['law']['max_abs_residual']:.4f}")
    for r in out["law"]["rows"]:
        print(f"   {r['site']}  n={r['n']:>6,}  reported={r['reported']:.4f}  "
              f"law={r['law']:.4f}  residual={r['residual']:+.4f}")

    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    targets = {"catalogue": qf, "sgmc_off": sgmc & (d_qf > dti_eval.R_PX)}

    prob = np.load(ROOT / ".cache" / "prob_final.npy")
    covered = np.isfinite(prob)
    flat = np.where(covered, np.nan_to_num(prob), 0.0)
    smooth = np.where(covered, gaussian_filter(flat, 2.0), 0.0).astype(np.float32)
    near = np.exp(-0.5 * ((d_qf - 12.0) / 14.0) ** 2)
    smooth = smooth * (0.15 + 0.85 * near.astype(np.float32))
    domain = footprint & covered
    del prob, flat

    G_org = out["law"]["G_implied_hidden_cells"]
    grid = [40_000, 60_000, 100_000, 160_000, 250_000]
    rows = []
    for n in grid:
        base = jittered_design(smooth, domain, n, tilt=0.35, seed=20261031)
        for kind in ("dot", "ribbon"):
            mask = base
            if kind == "ribbon":
                mask = binary_dilation(base, np.ones((3, 3), bool))
            nn = int(mask.sum())
            rec = {"n_requested": n, "emission": kind, "n_cells": nn}
            for name, tgt in targets.items():
                t = dti_eval.dti_terms(mask.astype(np.float32), tgt)
                r_cov = t["T"] / t["G"]
                f_cell = t["F"] / nn
                # scale-free reading: coverage and per-cell false mass transfer
                dti_hat = (r_cov * G_org) / (
                    0.2 * r_cov * G_org + 0.2 * f_cell * nn + 0.8 * G_org * (1 - r_cov))
                rec[name] = dict(DTI=round(t["DTI"], 4), T=round(t["T"], 1),
                                 F=round(t["F"], 1), coverage_r=round(r_cov, 4),
                                 false_mass_per_cell=round(f_cell, 4),
                                 DTI_scaled_to_Gorg=round(dti_hat, 4))
            rec["mean_DTI_scaled"] = round(
                float(np.mean([rec[k]["DTI_scaled_to_Gorg"] for k in targets])), 4)
            rows.append(rec)
            print(f"n={n:>7,} {kind:<6} cells={nn:>7,}  "
                  + "  ".join(f"{k}: DTI={rec[k]['DTI']:.4f} r={rec[k]['coverage_r']:.3f} "
                              f"f={rec[k]['false_mass_per_cell']:.3f} "
                              f"hat={rec[k]['DTI_scaled_to_Gorg']:.3f}" for k in targets)
                  + f"  mean_hat={rec['mean_DTI_scaled']:.3f}", flush=True)
            del mask
        del base

    best = max(rows, key=lambda r: r["mean_DTI_scaled"])
    out["sweep"] = rows
    out["best_by_scaled_estimate"] = dict(n_requested=best["n_requested"],
                                          emission=best["emission"],
                                          mean_DTI_scaled=best["mean_DTI_scaled"])
    out["caveat"] = (
        "The scaled estimate assumes the design's coverage fraction and per-cell false "
        "mass transfer from the proxy truth to the hidden truth. That holds only if the "
        "two fault networks have similar geometry and density; no proxy in this repository "
        "can test that assumption, because every proxy is either the catalogue the model "
        "was trained on or a compilation with a different mapping convention.")
    (ROOT / "evidence" / "emission_optimum.json").write_text(json.dumps(out, indent=1) + "\n")
    print("best:", json.dumps(out["best_by_scaled_estimate"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
