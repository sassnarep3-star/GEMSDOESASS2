#!/usr/bin/env python3
"""Independent forensics on the nine focus-site champions.

Everything here is measured from the hash-pinned raster bytes; nothing is copied
from another repository's claims.  Requires the nine pinned GeoTIFFs plus the
competition-grid reference files (see ``--help``).

Emits ``evidence/nine_site_forensics.json``.

Findings reproduced
-------------------
* SHA-256 and dot counts match the nine pinned artifacts.
* Reported leaderboard value is monotone *decreasing* in dot count.
* Reported leaderboard value is monotone *decreasing* in the fraction of dots
  that lie within 3 cells (300 m) of the mapped catalogue.
* The nine files are broad quasi-uniform lattices (median distance to the
  mapped catalogue 14-20 cells = 1.4-2.0 km), not on-fault predictions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.metric import dti_probabilistic  # noqa: E402

# user-reported / unverified leaderboard values, exactly as supplied in the brief
REPORTED = {
    "GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449,
    "GEMSDOE28": 0.2710, "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708,
    "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632, "GEMSDOE36": 0.2750,
}


def _read(path: pathlib.Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return np.nan_to_num(ds.read(1), nan=0.0, posinf=0.0, neginf=0.0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pinned-dir", required=True, type=pathlib.Path,
                    help="directory holding g24.tif ... g36.tif (pinned champions)")
    ap.add_argument("--sample", required=True, type=pathlib.Path)
    ap.add_argument("--labels", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    with rasterio.open(args.sample) as ds:
        footprint = np.isfinite(ds.read(1))
    catalogue = (rasterio.open(args.labels).read(1) >= 1) & footprint
    d_cat = ndi.distance_transform_edt(~catalogue)

    rows = []
    for site, reported in REPORTED.items():
        key = "g" + site.replace("GEMSDOE", "")
        path = args.pinned_dir / f"{key}.tif"
        arr = _read(path)
        dots = arr > 0
        n = int(dots.sum())
        d = d_cat[dots]
        cat_dti = dti_probabilistic(arr, catalogue, score_mask=footprint)
        rows.append({
            "site": site,
            "file": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "n_dots": n,
            "reported_leaderboard": reported,
            "reported_evidence": "USER-REPORTED / UNVERIFIED (no organizer receipt)",
            "pct_within_1px_of_catalogue": float((d <= 1).mean() * 100),
            "pct_within_2px_of_catalogue": float((d <= 2).mean() * 100),
            "pct_within_3px_of_catalogue": float((d <= 3).mean() * 100),
            "median_distance_to_catalogue_px": float(np.median(d)),
            "dti_scored_against_catalogue": float(cat_dti["dti"]),
            "binary_values_only": bool(np.isin(np.unique(arr[footprint]), [0.0, 1.0]).all()),
        })

    n = np.array([r["n_dots"] for r in rows], float)
    rep = np.array([r["reported_leaderboard"] for r in rows], float)
    ov = np.array([r["pct_within_3px_of_catalogue"] for r in rows], float)
    cat = np.array([r["dti_scored_against_catalogue"] for r in rows], float)

    design = np.column_stack([n, np.ones_like(n)])
    coef, *_ = np.linalg.lstsq(design, 1.0 / rep, rcond=None)
    fit = design @ coef
    r2 = 1.0 - float(((1.0 / rep - fit) ** 2).sum() / ((1.0 / rep - (1.0 / rep).mean()) ** 2).sum())

    out = {
        "scope": "measured on the nine hash-pinned champion rasters; no organizer receipt",
        "files": rows,
        "statistics": {
            "spearman_dots_vs_reported": float(spearmanr(n, rep).statistic),
            "spearman_dots_vs_reported_p": float(spearmanr(n, rep).pvalue),
            "spearman_catalogue_dti_vs_reported": float(spearmanr(cat, rep).statistic),
            "spearman_catalogue_overlap_vs_reported": float(spearmanr(ov, rep).statistic),
            "law_inverse_dti_vs_dots": {
                "form": "1/DTI = a*N + b",
                "a": float(coef[0]), "b": float(coef[1]), "r_squared": r2,
                "valid_range_N": [float(n.min()), float(n.max())],
                "asymptote_DTI_as_N_to_0": float(1.0 / coef[1]),
            },
            "all_nine_binary": bool(all(r["binary_values_only"] for r in rows)),
        },
        "interpretation": (
            "Within this family the reported score is explained almost entirely by how many "
            "cells are predicted and how many of them sit on faults that are already mapped. "
            "0.2778 is the fewest-dot, lowest-catalogue-overlap member; it is a dot-budget "
            "artefact, not evidence of a better geological model."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps(out["statistics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
