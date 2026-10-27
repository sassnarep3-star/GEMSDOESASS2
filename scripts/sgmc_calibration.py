#!/usr/bin/env python3
"""SGMC off-catalogue diagnostic + live-score calibration.

Instrument: truth = USGS SGMC geologic-map fault pixels that are > 3 px from
the competition catalogue (faults known to geology but absent from the
competition's mask — a fair proxy for 'missing faults').  Known catalogue is
masked pixel-exactly, exactly like the organizer's scoring note.  Neither
our candidate nor any registry raster was fit to SGMC, so the comparison is
leak-free in both directions (unlike hide-and-recover, which structurally
punishes any raster B=2-pruned against the full catalogue — IR-SASS2-01).

Calibration: regress OWNER-REPORTED live scores of the 9-site registry
rasters on their SGMC-DTI; map our candidate's SGMC-DTI through the fit.
Output is an ESTIMATE with explicit extrapolation caveats, never a score.
"""
import json
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "src"))

from gems.io_grid import REGISTRY_CACHE, load_bridge, read_band
from gems.metric import dti_binary

SGMC = os.path.join(REGISTRY_CACHE,
                    "GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif")


def main(candidate_tif):
    cat, footprint = load_bridge()
    sgmc = read_band(SGMC) > 0
    dcat = distance_transform_edt(~cat)
    truth = sgmc & footprint & (dcat > 3.0)
    score_mask = footprint & ~cat
    print(f"SGMC off-catalogue truth pixels: {int(truth.sum())}")

    man = json.load(open(os.path.join(REPO, "registry", "registry_manifest.json")))
    pts = []
    for r in man["rasters"]:
        arr = np.nan_to_num(read_band(os.path.join(REGISTRY_CACHE, r["path"])),
                            nan=0.0) > 0.5
        res = dti_binary(arr, truth, score_mask)
        pts.append(dict(name=f"{r['site']}:{r['name']}",
                        live=r["owner_reported_score"],
                        sgmc_dti=round(res["dti"], 5)))
        print(f"  {pts[-1]['sgmc_dti']:.5f}  live={r['owner_reported_score']:.4f}  {r['site']}")

    ours = np.nan_to_num(read_band(candidate_tif), nan=0.0) > 0.5
    ours_res = dti_binary(ours, truth, score_mask)
    print(f"  OURS sgmc_dti = {ours_res['dti']:.5f}")

    x = np.array([p["sgmc_dti"] for p in pts])
    y = np.array([p["live"] for p in pts])
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    s = float(np.std(resid, ddof=2))
    est = a + b * ours_res["dti"]
    # also simple ratio vs champion for a second opinion
    champ = [p for p in pts if "CHAMPION" in p["name"]][0]
    ratio_est = 0.2778 * ours_res["dti"] / max(champ["sgmc_dti"], 1e-9)
    out = dict(
        label="ESTIMATE (SGMC-off-catalogue calibration). NOT a leaderboard score.",
        instrument="SGMC-DTI: truth=SGMC faults >3px off catalogue; catalogue masked pixel-exact; pooled DTI a=0.2 b=0.8 300m kernel",
        candidate_sgmc_dti=round(float(ours_res["dti"]), 5),
        regression=dict(intercept=round(float(a), 4), slope=round(float(b), 4),
                        resid_std=round(s, 4), n_points=len(pts),
                        pearson=round(float(np.corrcoef(x, y)[0, 1]), 3)),
        estimate_regression=round(float(est), 4),
        estimate_band=[round(float(est - 2 * s), 4), round(float(est + 2 * s), 4)],
        estimate_champion_ratio=round(float(ratio_est), 4),
        caveats=[
            "All 9 calibration points are OWNER-REPORTED scores of one raster family (live range 0.2449-0.2778); extrapolation outside that band is unreliable.",
            "SGMC faults are a proxy for the hidden truth, not the hidden truth.",
        ],
        points=pts,
    )
    with open(os.path.join(REPO, "evidence", "sgmc_calibration.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({k: out[k] for k in ["candidate_sgmc_dti", "estimate_regression",
                                          "estimate_band", "estimate_champion_ratio",
                                          "regression"]}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
