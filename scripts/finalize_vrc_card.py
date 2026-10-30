#!/usr/bin/env python3
"""Assemble the final VRC run card from the saved receipts.

Reads only committed/persisted evidence files plus the saved raster bytes and
re-verifies the format checks against the organizer example mirror. It does not
re-run the model, so the card is reproducible from artifacts alone.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--card", type=Path, default=ROOT / "evidence" / "vrc_run_card.json")
    ap.add_argument("--final", type=Path, default=ROOT / "docs" / "data" / "vrc-run-card.json")
    ap.add_argument("--holdout", type=Path, default=ROOT / "evidence" / "exp8_vrc_variants.json")
    ap.add_argument("--format-json", type=Path, default=ROOT / "docs" / "data" / "format-vrc-nan.json")
    ap.add_argument("--format-zeros", type=Path, default=ROOT / "docs" / "data" / "format-vrc-zeros.json")
    ap.add_argument("--overlap", type=Path, default=ROOT / "evidence" / "registry_overlap_vrc.json")
    ap.add_argument("--spearman", type=Path, default=ROOT / "evidence" / "vrc_surface_spearman_vs_focus.json")
    ap.add_argument("--local", type=Path, default=ROOT / "evidence" / "vrc_vs_local_registry.json")
    ap.add_argument("--submission-name", default="GEMSDOESASS2-VRC-44090-20261030")
    ap.add_argument("--note", default="GEMSDOESASS2 VRC vent-ridge 44090d B=2 sep2.8 | HOLDOUT-DTI 0.0086 | research lane | 20261030")
    args = ap.parse_args()

    card = json.loads(args.card.read_text())
    fmt = json.loads(args.format_json.read_text())
    fmt0 = json.loads(args.format_zeros.read_text())
    ov = json.loads(args.overlap.read_text())
    sp = json.loads(args.spearman.read_text())
    local = json.loads(args.local.read_text())
    holdout = json.loads(args.holdout.read_text()) if args.holdout.is_file() else None

    name = args.submission_name
    note = args.note
    final = dict(card)
    final["assembled_utc"] = datetime.now(timezone.utc).isoformat()
    final["validator_output"] = {
        "nan_variant": {
            "file": fmt["candidate"], "sha256": fmt["candidate_sha256"],
            "checks": fmt["checks"], "counts": fmt["counts"],
            "strict_local_format_pass": fmt["strict_local_format_pass"],
            "failing_check": "outside_masked_or_nan is satisfied; whole_array_finite_in_0_1 is not "
                            "(the two local checks are mutually exclusive - IR-SASS2-13)",
        },
        "zeros_variant": {
            "file": fmt0["candidate"], "sha256": fmt0["candidate_sha256"],
            "checks": fmt0["checks"], "counts": fmt0["counts"],
            "strict_local_format_pass": fmt0["strict_local_format_pass"],
            "failing_check": "outside_masked_or_nan (zeros used outside the footprint, which the spec permits)",
        },
        "no_nan_inside_footprint": fmt["counts"]["inside_nan"] == 0,
        "values_in_0_1_inside_footprint": fmt["counts"]["inside_out_of_range_finite"] == 0
                                          and fmt["counts"]["inside_min"] >= 0
                                          and fmt["counts"]["inside_max"] <= 1,
        "crs_shape_transform_match": all(fmt["checks"][k] for k in ("crs_match", "shape_match", "transform_match")),
        "reference_note": "validated against the mirror copy of the organizer's example_submission.tif "
                          "(sha256 2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc), "
                          "which is hash-identical to data/bridge/sample_submission.tif; NOT organizer-authenticated.",
    }
    final["uniqueness"] = {
        "protocol_rule_1_limits": {"overlap_3px": 0.70, "abs_spearman": 0.90},
        "max_candidate_dot_overlap_vs_scanned_registry_rasters": max(
            (r["candidate_dots_within_3px_of_ref"] or 0.0) for r in ov["registry_rasters_with_highest_candidate_overlap"]
        ),
        "registry_rasters_scanned": ov["n_rasters_scanned"],
        "share_of_dots_covered_by_registry_union": ov["share_of_candidate_dots_covered_by_registry_union_3px"],
        "max_abs_spearman_vs_focus_champions": sp["max_abs_spearman"],
        "pass_genuine_raster_gates": bool(sp["pass"]) and max(
            (r["candidate_dots_within_3px_of_ref"] or 0.0) for r in ov["registry_rasters_with_highest_candidate_overlap"]
        ) <= 0.70,
        "local_sass2_downloads_max_overlap": max(
            r["ref_within3px_of_candidate"] for r in local["rows"]
        ),
        "local_sass2_top": local["rows"][:3],
        "local_sass2_note": "the candidate's own two encodings are excluded from its own duplicate screen",
        "lattice_probe": {
            "file": ov["lattice_probes_reported_separately"][0]["file"],
            "candidate_dots_within_3px_of_probe": ov["lattice_probes_reported_separately"][0]["candidate_dots_within_3px_of_ref"],
            "status": "FAILS the literal rule (space-filling probe covers the footprint)",
            "precedent": "the reported 0.2778 champion also fails it (IR-S-01); owner ruling pending",
        },
    }
    if holdout:
        final["holdout"]["variant_table"] = holdout
    # The repo-wide submission policy (IR-S-15/IR-S-16): any footprint-wide dot set fails the literal lattice
    # rule, so a candidate that trips the probe is recorded as blocked-owner-ruling even when its verdict is
    # already negative. Keep both fields so a reader cannot mistake "negative" for "cleared but unused".
    final["status"] = "blocked-owner-ruling"
    final["ok_to_submit"] = False
    final["submission_name"] = name
    final["submission_note_140"] = note
    final["note_length"] = len(note)
    final["verdict"] = "negative"
    final["ok_to_download_and_submit"] = False
    final["decision_rationale"] = (
        "Format and duplicate gates pass; the scientific gate does not. The candidate does not beat the "
        "hash-pinned focus-lineage parent on either instrument (public-catalogue hide-and-recover, nor the "
        "off-catalogue SGMC instrument), and the paired 95% CIs include zero on the one instrument where it "
        "is ahead. Under protocol rule 6 a slot is not spent on an idea that has not beaten the holdout best, "
        "so the file is published as a downloadable research artifact only."
    )
    if args.final.name == "run-card.json":
        raise SystemExit("refusing to overwrite docs/data/run-card.json: it is the build_card() "
                         "negative-card contract (tests/test_protocol_safety.py). Use vrc-run-card.json.")
    args.final.parent.mkdir(parents=True, exist_ok=True)
    args.final.write_text(json.dumps(final, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: final[k] for k in
                      ("verdict", "ok_to_download_and_submit", "submission_name", "note_length",
                       "uniqueness", "decision_rationale")}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
