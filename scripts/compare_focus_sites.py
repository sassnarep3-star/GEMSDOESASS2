#!/usr/bin/env python3
"""Head-to-head: every focus-site champion raster vs the new candidate, on
identical local targets, with a matched random-lattice control.

Why this exists
---------------
The leaderboard truth is hidden, so "will this beat 0.2778?" can only be
answered by comparing candidates on *local* targets that stand in for it.
Two are used, and they bracket the problem:

``catalogue``   QFaults/INGENIOUS labels (what the training data contains).
``sgmc_off``    USGS SGMC faults >3 px outside the catalogue (a different
                mapping programme -- the closest local analogue of "faults
                somebody else mapped that the labels do not contain").

The control is the decisive part.  A dot lattice scores non-zero on both
targets purely by geometric luck, so a candidate is only better than the
0.2778 champion if it beats the champion's *ratio to a matched random
lattice* on both targets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import dti_eval  # noqa: E402

SITES = {
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
REPORTED = {"GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449,
            "GEMSDOE28": 0.2710, "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708,
            "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632, "GEMSDOE36": 0.2750}
SITE_ROOT = Path("/tmp/sites")


def load_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(ROOT / ".cache" / "external" / "derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    qf = labels >= 1
    d_qf = distance_transform_edt(~qf)
    sgmc_off = sgmc & (d_qf > dti_eval.R_PX)
    targets = {"catalogue": qf, "sgmc_off": sgmc_off}

    rows = []
    rng = np.random.default_rng(7)
    for site, rel in SITES.items():
        p = SITE_ROOT / rel
        if not p.exists():
            print(f"SKIP {site}: {p} missing")
            continue
        mask = load_mask(p)
        n = int(mask.sum())
        rec = {"site": site, "file": rel, "reported": REPORTED[site], "n_cells": n}
        for name, tgt in targets.items():
            rec[name] = dti_eval.dti_terms(mask.astype(np.float32), tgt)
        # matched random-lattice control: same number of cells, uniform over
        # the surveyed footprint (the same domain every site placed dots in)
        with rasterio.open(ROOT / ".cache" / "features" / "training_features.tif") as ds:
            cov = ds.read(1) > -1e38
        flat = np.flatnonzero(cov.ravel())
        pick = rng.choice(flat, size=n, replace=False)
        ctrl = np.zeros(cov.shape, bool)
        ctrl.ravel()[pick] = True
        for name, tgt in targets.items():
            rec[f"{name}_control"] = dti_eval.dti_terms(ctrl.astype(np.float32), tgt)
        for name in targets:
            c = rec[f"{name}_control"]["DTI"]
            rec[f"{name}_lift"] = (rec[name]["DTI"] / c) if c > 0 else None
        rows.append(rec)
        print(f"{site:10s} n={n:6d} reported={rec['reported']:.4f} "
              f"DTIcat={rec['catalogue']['DTI']:.4f} (x{rec['catalogue_lift']:.2f}) "
              f"DTIsgmc={rec['sgmc_off']['DTI']:.4f} (x{rec['sgmc_off_lift']:.2f})",
              flush=True)

    out = {"targets": {"n_catalogue": int(qf.sum()), "n_sgmc_off": int(sgmc_off.sum())},
           "evaluator_version": "EXACT-DTI-alpha0.2-beta0.8-R3px-v1",
           "rows": rows,
           "note": ("All scores are OWNER-REPORTED. Local DTI values are measured "
                    "against local proxies, not the hidden test set, and are not "
                    "leaderboard scores.")}
    (ROOT / "evidence" / "candidate_vs_focus_sites.json").write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
