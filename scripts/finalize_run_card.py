#!/usr/bin/env python3
"""Uniqueness gate + score-estimate table + run card for the promoted raster.

Uniqueness is measured exactly as the project protocol defines it:
  * max |Spearman rho| of the two surfaces over the footprint  (limit 0.90)
  * % of OUR positive cells within 3 px of a registry raster's cells (limit 70)
  * % of THEIR cells within 3 px of ours (reported for context -- with a dense
    design this is large by construction and is NOT the protocol's criterion)

Score estimation is explicit about its assumption.  The official identity is

    DTI = T / (0.2 T + 0.2 F + 0.8 |G|)

`c = T/|G|` (the k-weighted fraction of the truth covered) is a property of the
prediction's spatial footprint and the target's *geometry*, so it is measured on
two local proxies; |G| is then swept because it cannot be measured locally.
Nothing here is an organizer score.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402
from gems_sass2.submission import sha256_file  # noqa: E402

import argparse

DEFAULT_CAND = ROOT / "docs" / "downloads" / "gemsass2-catfree-300k-20261031-zeros.tif"
SITE_ROOT = Path("/tmp/sites")
REGISTRY = {
    "GEMSDOE24": "GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
    "GEMSDOE25": "GEMSDOE32/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
    "GEMSDOE27": "GEMSDOE27/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
    "GEMSDOE28": "GEMSDOE28/docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif",
    "GEMSDOE30": "GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
    "GEMSDOE32": "GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}
OWN_PRIOR = {
    "ass2-strainridge": "docs/downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif",
    "ass2-hvfd-exp3": "docs/downloads/gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif",
    "ass2-thermo-tilt": "docs/downloads/gemsdoesass2-thermo-tilt-conduit-37654-20261027T113705Z-d8f85365-zeros.tif",
}


def load(path: Path):
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.where(np.isfinite(a), a, 0.0).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", type=Path, default=DEFAULT_CAND)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "final_run_card.json")
    args = ap.parse_args()
    cand = load(args.candidate)
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / "data" / "bridge" / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    sgmc_off = sgmc & (d_qf > dti_eval.R_PX)

    ours = cand > 0
    rng = np.random.default_rng(5)
    sample = rng.choice(np.flatnonzero(foot.ravel()), 200_000, replace=False)
    a_c = cand.ravel()[sample]
    d_ours = distance_transform_edt(~ours)

    rows = []
    for label, rel in list(REGISTRY.items()) + list(OWN_PRIOR.items()):
        p = SITE_ROOT / rel if label in REGISTRY else ROOT / rel
        if not p.exists():
            rows.append({"name": label, "status": "missing"})
            continue
        b = load(p)
        theirs = b > 0
        d_theirs = distance_transform_edt(~theirs)
        rho = float(spearmanr(a_c, b.ravel()[sample]).statistic)
        rows.append({
            "name": label,
            "their_cells": int(theirs.sum()),
            "ours_within3px_of_theirs_pct": float(100 * (d_theirs[ours] <= 3).mean()),
            "theirs_within3px_of_ours_pct": float(100 * (d_ours[theirs] <= 3).mean()),
            "spearman_full_surface": rho,
        })
        print(f"{label:22s} n={theirs.sum():>6,} ours->theirs(3px)={rows[-1]['ours_within3px_of_theirs_pct']:6.2f}% "
              f"theirs->ours={rows[-1]['theirs_within3px_of_ours_pct']:6.2f}% rho={rho:+.4f}", flush=True)

    valid = [r for r in rows if "spearman_full_surface" in r]
    gate = {
        "max_abs_spearman": max(abs(r["spearman_full_surface"]) for r in valid),
        "max_pct_ours_within3px_of_one_registry": max(r["ours_within3px_of_theirs_pct"] for r in valid),
        "spearman_limit": 0.90,
        "overlap_limit_pct": 70.0,
    }
    gate["passes"] = bool(gate["max_abs_spearman"] <= 0.90
                          and gate["max_pct_ours_within3px_of_one_registry"] <= 70.0)

    # --- score estimate: c measured, |G| swept -------------------------
    terms = {n: dti_eval.dti_terms(cand, t) for n, t in (("catalogue", qf), ("sgmc_off", sgmc_off))}
    n_cells = int(ours.sum())
    est = {"n_cells": n_cells, "terms": terms, "table": []}
    for name, t in terms.items():
        c = t["T"] / t["G"]
        for g in (25_000, 35_000, 60_000, 120_000):
            f = t["F"]
            dti = c / (0.2 * c + 0.2 * f / g + 0.8)
            est["table"].append({"proxy": name, "assumed_G": g, "c": round(c, 4),
                                 "implied_DTI": round(dti, 4)})
            print(f"proxy={name:9s} G={g:>7,} c={c:.4f} F={f:,.0f} -> implied DTI {dti:.4f}")
        # the nine-site law implies |G| ~ 51,734; that is the best-scaled single value
        g_law = 51_734.0
        est[f"law_consistent_{name}"] = round(c / (0.2 * c + 0.2 * t["F"] / g_law + 0.8), 4)

    out = {"file": str(args.candidate.resolve().relative_to(ROOT)), "sha256": sha256_file(args.candidate),
           "n_cells": n_cells, "uniqueness": {"gate": gate, "per_raster": rows},
           "score_estimate": est,
           "note": ("MODEL ESTIMATE, not a leaderboard score. c is measured on local "
                    "proxies; |G| is swept because it is not locally identifiable.")}
    args.out.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(gate, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
