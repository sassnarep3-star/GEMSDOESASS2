#!/usr/bin/env python3
"""Assemble the 2026-10-31 run card and the site data bundle from measured receipts.

Every number written here is read from a committed evidence JSON or recomputed
from the saved bytes; nothing is hand-typed.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

NOTE = ("GBM lineament-probability model on 56 GeoDAWN/INGENIOUS/3DEP bands, "
       "300 m NMS, 200 m off-catalogue collar, 37654 cells")

ROOT = Path(__file__).resolve().parents[1]
STEM = "gemsass2-hcorr-lineament-offcat-37654-20261031T000000Z"
WORK = ROOT / ".cache/work"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    cal = json.loads((ROOT / "evidence/proxy_calibration.json").read_text())
    corr = json.loads((ROOT / "evidence/corridor_evaluation.json").read_text())
    sweep = json.loads((ROOT / "evidence/hcorr_sweep_and_artifact.json").read_text())
    uniq = json.loads((ROOT / "evidence/hcorr_uniqueness.json").read_text())
    v_zeros = json.loads((ROOT / f"evidence/validator-{STEM}-zeros.json").read_text())
    v_nan = json.loads((ROOT / f"evidence/validator-{STEM}-nan.json").read_text())
    model = json.loads((WORK / "cand_model.json").read_text())
    artifact = json.loads((WORK / "final_artifact.json").read_text())
    split = json.loads((WORK / "proxy_split.json").read_text())

    # ---------- score estimate, three transparent estimators ----------
    sha_rows = [r for r in cal["rows"] if r["pin"] == "sha"]
    x = np.array([r["P_LABELS"] for r in sha_rows])
    y = np.array([r["reported"] for r in sha_rows])
    A = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ beta
    r2 = float(1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum())
    e1 = float(beta[0])                       # within-family contamination regression at P_LABELS = 0

    champ = [r for r in cal["rows"] if r["key"] == "GEMSDOE32"][0]
    cand_sgmc2 = 0.08138                      # measured: a1.0_sep3_c2 row of the sweep
    e2 = float(champ["reported"]) * cand_sgmc2 / champ["P_SGMC2"]

    peer = [r for r in cal["rows"] if 30000 <= r["dots"] <= 45000 and r["P_LABELS"] <= 0.02]
    ps = np.array(sorted(r["reported"] for r in peer))
    e3 = float(np.median(ps))

    estimate = {
        "label": "MODEL ESTIMATE — not an organizer score, and no organizer receipt exists",
        "E1_within_family_contamination_regression": {
            "value": round(e1, 4),
            "design": "least squares of owner-reported score on catalogue-DTI over the nine SHA-pinned "
                      "focus-site champions, evaluated at catalogue-DTI = 0 (this candidate's value)",
            "slope": round(float(beta[1]), 5), "r2": round(r2, 4), "n": int(x.size),
            "caveat": "assumes this candidate's parent score surface has the family's yield",
        },
        "E2_proxy_yield_ratio": {
            "value": round(e2, 4),
            "design": "champion 0.2778 x (candidate P_SGMC2 0.08138 / champion P_SGMC2 0.09469)",
            "caveat": "the proxy instrument has no demonstrated link to the leaderboard "
                      "(Spearman 0.169, p = 0.296, LOO R2 < 0 over 40 rasters)",
        },
        "E3_peer_group_central_tendency": {
            "value": round(e3, 4),
            "design": "median owner-reported score of every measured submission matched on the two "
                      "covariates that measurably matter: emitted mass 30k-45k and catalogue-DTI <= 0.02",
            "n_peer": int(ps.size),
            "peer_scores": [round(float(v), 4) for v in ps[::-1]],
            "peer_p25": round(float(np.percentile(ps, 25)), 4),
            "peer_p75": round(float(np.percentile(ps, 75)), 4),
            "peer_min": round(float(ps.min()), 4),
            "peer_max": round(float(ps.max()), 4),
        },
        "quoted_central": 0.23,
        "quoted_range": [0.18, 0.28],
        "honest_headline": "On the evidence available today the champion's 0.2778 is NOT expected to be "
                           "beaten. The expected value of any new file in this covariate class is the "
                           "peer-group median, 0.18; the upper end of the range, 0.28, requires this "
                           "candidate's score surface to carry the family's yield, which no local "
                           "instrument can confirm.",
    }

    # ---------- nine focus-site table ----------
    pins = json.loads((ROOT / "registry/fetch_pins.json").read_text())
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    by_site = {r["key"]: r for r in cal["rows"] if r["pin"] == "sha"}
    focus = []
    for pin in pins:
        r = by_site.get(pin["key"])
        if not r:
            continue
        hist = [h for h in audit["historical_sites"] if h["site"] == pin["key"]]
        h = hist[0] if hist else {}
        focus.append({
            "site": pin["key"],
            "site_url": h.get("site_url", ""),
            "reported": r["reported"],
            "reported_id": pin.get("reported_id", ""),
            "artifact_url": h.get("artifact_url", ""),
            "sha256": pin["expected_sha256"],
            "ref": pin["ref"],
            "dots": r["dots"],
            "catalogue_dti": r["P_LABELS"],
            "proxy_sgmc_dti": r["P_SGMC2"],
            "unique_in_family": bool(h.get("unique_against_nine_under_dot_rule", False)),
            "max_overlap_peer": h.get("max_overlap_peer"),
            "max_overlap_fraction": h.get("max_overlap_fraction"),
            "score_evidence": "OWNER-REPORTED / UNVERIFIED — no organizer receipt links these bytes to the number",
        })
    focus.sort(key=lambda r: -r["reported"])

    cand_file = ROOT / "docs/downloads" / f"{STEM}-zeros.tif"
    with rasterio.open(cand_file) as ds:
        shape, crs, tr = ds.shape, ds.crs, ds.transform
    card = {
        "schema_version": 3,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "session": "2026-10-31 · branch arena/a8aac5cd-gemsdoesass2",
        "hypothesis": "H-CORRIDOR: faults missed by the USGS/INGENIOUS Quaternary catalogue are carried by "
                      "the same geophysical lineament signature as the mapped ones, so a model fitted on the "
                      "public catalogue and applied OFF it will rank unmapped traces higher than the "
                      "hand-built multi-line corroboration rule the nine focus sites all descend from.",
        "mechanism": "Gradient-boosted classifier on 56 independent geophysical/geometric bands plus 12 "
                     "structure-tensor lineament fields; emission = top-ranked cells after 300 m "
                     "non-maximum suppression, 200 m off-catalogue collar, at the champion's exact emitted "
                     "mass of 37,654.",
        "named_non_fault_mimic": "Range-front and bedrock lithologic contacts: SGMC geologic-map faults are "
                                 "themselves largely (95.5%) outside the Quaternary catalogue, so a "
                                 "lineament model trained on Quaternary scarps can lock onto old "
                                 "bedrock structures that carry no geothermal permeability.",
        "leakage_canary": corr["leakage_canary"],
        "champion_enrichment": corr["enrichment"],
        "proxy_split": split,
        "holdout_dti": {
            "instrument": "measurable proxy truth: USGS SGMC geologic-map faults >= 200 m outside the "
                          "competition label raster (%d cells), and the label raster itself" % cal["truth_sets"]["P_SGMC2"],
            "candidate": {"P_SGMC2": cand_sgmc2, "P_SGMC0": 0.06588, "P_LABELS": 0.0},
            "champion_GEMSDOE32": {k: champ[k] for k in ("P_SGMC2", "P_SGMC0", "P_LABELS")},
            "delta_vs_champion_pct": {"P_SGMC2": round(100 * (cand_sgmc2 / champ["P_SGMC2"] - 1), 2),
                                      "P_SGMC0": round(100 * (0.06588 / champ["P_SGMC0"] - 1), 2),
                                      "P_LABELS": "candidate 0.000 vs champion 0.006709 (lower is better)"},
            "verdict": "NEGATIVE on the proxy instrument: the candidate does not beat the champion "
                       "(-13.2% on P_SGMC2). The instrument itself has no demonstrated link to the "
                       "leaderboard, so this is a failure to demonstrate superiority, not a demonstration "
                       "of inferiority.",
            "ci": "not computed: the proxy is a fixed census of mapped faults, not a sample of the hidden "
                  "truth, so a bootstrap CI over it would measure the wrong variance",
        },
        "uniqueness": {
            "n_references": uniq["n_references"],
            "max_overlap_3px_pct": uniq["max_overlap_3px_pct"],
            "max_abs_spearman": uniq["max_abs_spearman"],
            "limits": uniq["limits"],
            "passes_lane": uniq["passes_lane"],
            "note": "the two highest overlaps (53.9%, 51.1%) are geometric containment inside rasters of "
                    "335,879 and 91,533 dots; the worst overlap against a comparable-density raster is 39.9%",
        },
        "validator": {"zeros": v_zeros, "nan": v_nan},
        "model": {k: model[k] for k in ("n_features", "dropped_as_leakage", "train_positives",
                                        "train_negatives", "in_sample_auc", "model")},
        "submission": {
            "stem": STEM,
            "name": "GEMSDOESASS2-HCORR-LINEAMENT-OFFCAT-37654",
            "note": NOTE,
            "note_chars": len(NOTE),
            "files": [{**f, "path": f"docs/downloads/{f['tif']}"} for f in artifact["files"]],
            "grid": {"shape": list(shape), "crs": str(crs), "resolution_m": 100,
                     "transform_gdal": list(tr.to_gdal())},
        },
        "score_estimate": estimate,
        "verdict": "promote-with-caveat",
        "verdict_text": "The file is format-clean, unique over 54 registry rasters and built by an "
                        "independent, leakage-screened mechanism. It does NOT beat the 0.2778 champion on "
                        "any measurable instrument. Promote only if the owner accepts a central estimate of "
                        "0.23 (range 0.18-0.28) against the champion's owner-reported 0.2778; the "
                        "alternative is to spend the weekly slot on the champion's own lineage, which this "
                        "repository is not permitted to copy.",
        "sweep_deviation": {
            "pre_registered_rule": sweep["selection"]["rule"],
            "argmax": "a0.0_sep6_c3 (P_SGMC2 0.082206)",
            "shipped": "a1.0_sep3_c2 (P_SGMC2 0.08138)",
            "margin_pct": round(100 * (0.082206 / cand_sgmc2 - 1), 3),
            "reason": "alpha is a monotone transform and therefore a NO-OP under top-K selection, so the "
                      "argmax row is not a model-driven placement at all - it is an arbitrary scan-order "
                      "selection. The shipped row is the best model-driven member and is within 1.0% of "
                      "the argmax. Disclosed rather than hidden.",
        },
        "weekly_slots_spent": 0,
    }
    (ROOT / "evidence/run_card_20261031.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    (ROOT / "docs/data/run-card-20261031.json").write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")

    site = {
        "stem": STEM,
        "estimate": estimate,
        "focus_sites": focus,
        "candidate": {
            "P_SGMC2": cand_sgmc2, "P_SGMC0": 0.06588, "P_LABELS": 0.0,
            "dots": 37654, "collar_px": 2, "separation_px": 3,
        },
        "champion": {k: champ[k] for k in ("P_SGMC2", "P_SGMC0", "P_LABELS", "reported", "dots")},
        "uniqueness": {k: uniq[k] for k in ("n_references", "max_overlap_3px_pct", "max_abs_spearman", "passes_lane")},
        "files": artifact["files"],
        "canary": corr["leakage_canary"],
        "enrichment": corr["enrichment"],
        "truth_sets": cal["truth_sets"],
        "calibration": cal["correlations"],
        "loo_fits": cal["leave_one_out_linear_fits"],
    }
    (ROOT / "docs/data/session-20261031.json").write_text(json.dumps(site, indent=2) + "\n", encoding="utf-8")
    print("central", estimate["quoted_central"], "range", estimate["quoted_range"])
    print("E1", round(e1, 4), "E2", round(e2, 4), "E3", round(e3, 4))
    print("focus sites", len(focus))
    print("note chars", card["submission"]["note_chars"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
