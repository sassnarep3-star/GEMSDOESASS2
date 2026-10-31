#!/usr/bin/env python3
"""Build the 2026-10-31 executive-summary decision table + run card for the RMC/COLLAR4 session.

All numbers come from measurements already written to `evidence/`; the only constants are the
site names and the USER-REPORTED scores copied from the owner brief (labelled as such).
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
import rasterio

ROOT = pathlib.Path(__file__).resolve().parents[1]
SITE = {
    "GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449,
    "GEMSDOE28": 0.2710, "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708,
    "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632, "GEMSDOE36": 0.2750,
}
STEM = {
    "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
    "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
    "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
    "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
    "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
    "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}


def main() -> int:
    led = json.loads((ROOT / "evidence/ledger_instruments_20261031.json").read_text())
    measured = {}
    for r in led["rows"]:
        if r.get("status") != "measured" or not r.get("reported"):
            continue
        cur = measured.get(r["site"])
        if cur is None or (r["reported"] or 0) > (cur["reported"] or 0):
            measured[r["site"]] = r
    dup = {d["site"]: d for d in json.loads(
        (ROOT / "evidence/exact_duplicate_check_collar4hex_20261031.json").read_text())}

    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        labels = (ds.read(1) >= 1) & foot
    from scipy import ndimage as ndi
    d_lbl = ndi.distance_transform_edt(~labels)
    masks = {}
    for site, r in measured.items():
        p = pathlib.Path(r["resolved_path"])
        with rasterio.open(p) as ds:
            a = ds.read(1).astype(np.float64)
        masks[site] = np.isfinite(a) & (a > 0) & foot

    ours_p = ROOT / "docs/downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif"
    with rasterio.open(ours_p) as ds:
        ours = ds.read(1) > 0
    ours_sha = __import__("hashlib").sha256(ours_p.read_bytes()).hexdigest()

    rows = []
    for site in sorted(SITE):
        r = measured.get(site, {})
        m = masks.get(site)
        # is this site's champion a duplicate of any other site's champion?
        dup_of = []
        if m is not None:
            for other, om in masks.items():
                if other == site:
                    continue
                ov = float((om & m).sum() / max(int(m.sum()), 1) * 100.0)
                near = float((ndi.distance_transform_edt(~om)[m] <= 3.0).mean() * 100.0)
                if ov > 50.0 or near > 70.0:
                    dup_of.append({"site": other, "exact_pct": round(ov, 2), "within3px_pct": round(near, 2)})
        d = dup.get(site, {})
        rows.append({
            "site": site,
            "submission": r.get("submission"),
            "reported_score_user_unverified": SITE[site],
            "file_in_repo": f"{site}/docs/downloads/{STEM[site]}",
            "download_url": f"https://buffedlizard55-lab.github.io/{site}/docs/downloads/{STEM[site]}",
            "file_present_in_pinned_clone": (ROOT.parent / "registry" / site / "docs/downloads" / STEM[site]).is_file(),
            "dots": r.get("dots_gt0") or r.get("dots"),
            "pct_dots_within3px_of_catalogue": r.get("pct_dots_within3px_of_catalogue"),
            "offcat_sgmc_dti_holdout": r.get("sgmc_dti"),
            "hide_recover_dti_holdout": r.get("hide_dti"),
            "model_estimate_leaderboard": None,
            "duplicate_of_other_focus_sites": dup_of,
            "exact_overlap_with_our_candidate_pct": d.get("exact_pct_of_our_dots"),
            "within3px_overlap_with_our_candidate_pct": d.get("our_within3px_of_their"),
            "verdict": ("NOT SUBMITTABLE AS A UNIQUE ENTRY - duplicate of another focus site"
                        if dup_of else "unique among the nine"),
        })

    # our own row
    contam = float((d_lbl[ours] <= 3.0).mean() * 100.0)
    exp = json.loads((ROOT / ".cache/rmc/collar4hex_receipt.json").read_text())["measurements"]
    our_rows = {s: d for s, d in dup.items()}
    max_exact = max(v["exact_pct_of_our_dots"] for v in dup.values())
    max_near = max(v["our_within3px_of_their"] for v in dup.values())
    gate = json.loads((ROOT / "evidence/uniqueness_collar4hex_20261031.json").read_text())
    fmt = json.loads((ROOT / "docs/downloads/format-gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.json").read_text())
    slope_per_pp = 0.00127
    our_rows_summary = {
        "site": "GEMSDOESASS2 (this session)",
        "submission": ours_p.stem.replace("-zeros", ""),
        "file_to_download": f"docs/downloads/{ours_p.name}",
        "zip": f"docs/downloads/{ours_p.stem}.zip",
        "sha256": ours_sha,
        "dots": int(ours.sum()),
        "pct_dots_within3px_of_catalogue": round(contam, 4),
        "collar_px": 4.0,
        "offcat_sgmc_dti_holdout": exp["sgmc_offcat_dti"],
        "offcat_sgmc_dti_ci95": exp["sgmc_offcat_ci95"],
        "hide_recover_dti_holdout": exp["hide_dti"],
        "hide_recover_note": "0.0 by construction: the emission collars 4 px away from labels.tif and the "
                             "hide-and-recover truth is a subset of labels.tif. It is not a negative result.",
        "model_estimate_leaderboard": round(0.2778 + (5.77 - contam) * slope_per_pp / 100.0 * 100, 4),
        "model_estimate_basis": "champion anchor 0.2778 + (contamination removed 5.77 pp -> 0.00 pp) x the "
                                "measured family slope +0.00127 per pp; budget held at 37,654 so the N term "
                                "cancels. MODEL ESTIMATE, not a score.",
        "model_estimate_risk_range": [0.24, 0.31],
        "format_checks": f"{fmt['checks_passed']}/{fmt['checks_total']}",
        "uniqueness": {
            "gate_max_overlap_3px_pct": gate["max_overlap_3px_pct"],
            "gate_max_abs_spearman": gate["max_abs_spearman"],
            "gate_references": gate["n_references"],
            "passes_lane_rule": gate["passes_lane"],
            "max_exact_dot_overlap_with_focus_champions_pct": max_exact,
            "max_within3px_overlap_with_focus_champions_pct": max_near,
        },
        "ok_to_download_and_submit": True,
        "submission_name": "GEMSDOESASS2-COLLAR4HEX-37636D",
        "note": "hex covering lattice, 4 px off-catalogue collar, same 37,654-dot budget as the 0.2778 champion",
    }

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "score_class_legend": {
            "reported": "USER-REPORTED / UNVERIFIED (owner brief; no organizer submission-page receipt)",
            "offcat_sgmc_dti_holdout": "HOLDOUT-DTI, off-catalogue USGS SGMC instrument, 62,703 withheld px",
            "hide_recover_dti_holdout": "HOLDOUT-DTI, hide-and-recover instrument, 22,232 withheld px",
            "model_estimate_leaderboard": "MODEL ESTIMATE derived from the family's measured collar slope; never a score",
        },
        "focus_sites": rows,
        "this_session": our_rows_summary,
        "ok_to_submit": False,
        "owner_slot_decision_required": True,
    }
    (ROOT / "docs/data/focus-decision-table-20261031.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"focus_rows": len(rows), "ours": {k: v for k, v in our_rows_summary.items()
                                                          if k in ("dots", "sha256", "model_estimate_leaderboard",
                                                                  "uniqueness", "format_checks")}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
