#!/usr/bin/env python3
"""Merge the SGMC calibration into the run card and set the final estimate.

The pipeline's raw champion-ratio on the as-submitted hide-and-recover arm
is structurally invalid for B=2-pruned rasters (IR-SASS2-01): the withheld
truth IS catalogue, which the prune deliberately avoids.  The final
estimate is therefore the band spanned by the two leak-free methods:
  low  = within-family SGMC regression (extrapolated; family range caveat)
  high = champion-ratio on the SGMC off-catalogue instrument
Point = mean of the two methods.  Always labeled ESTIMATE.
"""
raise SystemExit('Legacy release path disabled: its partial registry and private holdout do not satisfy the current protocol. See docs/research/concurrent-main.md and scripts/check_registry.py.')

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EV = os.path.join(REPO, "evidence")

card = json.load(open(os.path.join(EV, "run_card.json")))
sg = json.load(open(os.path.join(EV, "sgmc_calibration.json")))

lo = min(sg["estimate_regression"], sg["estimate_champion_ratio"])
hi = max(sg["estimate_regression"], sg["estimate_champion_ratio"])
point = round((lo + hi) / 2, 4)
card["estimated_live_score"] = {
    "label": "ESTIMATE — never a score. Band spans two leak-free methods on the SGMC off-catalogue instrument.",
    "point": point,
    "range": [lo, hi],
    "method_low": f"within-family regression (extrapolated): {sg['estimate_regression']}",
    "method_high": f"champion-ratio 0.2778 x (ours {sg['candidate_sgmc_dti']} / champ "
                   f"{[p['sgmc_dti'] for p in sg['points'] if 'CHAMPION' in p['name']][0]}): "
                   f"{sg['estimate_champion_ratio']}",
    "irregularities": [
        "IR-SASS2-01: as-submitted hide-and-recover ratio (0.0062) withdrawn — instrument structurally punishes B=2-pruned rasters (withheld truth IS catalogue); mirrors GEMSDOE32 IR-45-EVAL-02.",
        "IR-SASS2-02: EXP2 N-sweep selection not transferable (FP break-even at holdout DTI is ~14x looser than at live 0.2778); N kept at pre-registered 37,000.",
        "IR-SASS2-03: all 12 calibration points are one raster family in a 0.2449-0.2778 band; extrapolation to a unique raster is the main uncertainty.",
    ],
}
card["sgmc_diagnostic"] = sg
digest8 = card["raster_sha256"][:8]
h = card["holdout_dti"]["ours_visible_only"]["mean_dti"]
card["submission_note_140"] = (
    f"SASS2 SCU scarp-corridor-UTh 37000d B2 sep2 | SGMC {sg['candidate_sgmc_dti']:.3f} "
    f"vs champ 0.094 | HR {h:.4f} | est {lo:.2f}-{hi:.2f} | {digest8}")[:140]
assert len(card["submission_note_140"]) <= 140

with open(os.path.join(EV, "run_card.json"), "w") as f:
    json.dump(card, f, indent=2)
for audit in glob.glob(os.path.join(REPO, "docs", "downloads", "*-audit.json")):
    with open(audit, "w") as f:
        json.dump(card, f, indent=2)
print("note:", card["submission_note_140"], f"({len(card['submission_note_140'])} chars)")
print("estimate:", card["estimated_live_score"]["point"], card["estimated_live_score"]["range"])
print("verdict:", card["verdict"])
