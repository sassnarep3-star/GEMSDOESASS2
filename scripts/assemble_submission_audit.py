#!/usr/bin/env python3
"""Assemble the promoted-submission audit JSON from the saved evidence receipts.

Reads the run card, the strict validator output and the uniqueness sweep written by
`build_strain_ridge_submission.py`, `validate_tif.py` and `focus_uniqueness_check.py`,
then emits `docs/downloads/<stem>-audit.json` in the schema the site tests expect.

Nothing is recomputed here except the SHA-256 of the shipped bytes, so the audit can
never drift from the artifacts it describes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stem", required=True)
    ap.add_argument("--run-card", type=pathlib.Path, required=True)
    ap.add_argument("--uniqueness", type=pathlib.Path, required=True)
    ap.add_argument("--downloads", type=pathlib.Path, default=ROOT / "docs/downloads")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()

    card = json.loads(args.run_card.read_text())
    uniq = json.loads(args.uniqueness.read_text())
    zeros = json.loads((ROOT / f"evidence/validator-{args.stem}-zeros.json").read_text())
    nan = json.loads((ROOT / f"evidence/validator-{args.stem}-nan.json").read_text())

    zeros_tif = args.downloads / f"{args.stem}-zeros.tif"
    zeros_zip = args.downloads / f"{args.stem}-zeros.zip"
    nan_tif = args.downloads / f"{args.stem}-nan.tif"
    live_sha = sha256(zeros_tif)
    assert live_sha == zeros["candidate_sha256"], "shipped bytes do not match the validator receipt"
    assert live_sha == card["raster"]["sha256"], "shipped bytes do not match the run card"

    checks = zeros["checks"]
    passed = sum(1 for v in checks.values() if v)
    audit = {
        "hypothesis": card["hypothesis"],
        "mechanism": card["mechanism"],
        "named_non_fault_process": card["named_non_fault_process"],
        "holdout_dti": card["holdout"],
        "leakage_canary": {
            "max_single_feature_auc": card["holdout"]["leakage_canary_max_auc"],
            "threshold": 0.90,
            "passed": card["holdout"]["leakage_canary_max_auc"] < 0.90,
            "status": card["holdout"]["leakage_canary_verdict"],
        },
        "correlation_overlap_vs_registry": {
            "n_references": uniq["n_references"],
            "max_overlap_3px_pct": round(uniq["max_overlap_3px_pct"], 4),
            "max_abs_spearman": round(uniq["max_abs_spearman"], 6),
            "overlap_limit_pct": 70.0,
            "spearman_limit": 0.90,
            "passes_lane": bool(uniq["passes_lane"]),
            "top_overlaps": uniq["top_overlaps"][:6],
            "scope_note": (
                "Compared against the nine hash-pinned focus-site champions plus every local "
                "download. The wider GEMSDOE corpus (~90 sites) is not mirrored locally."
            ),
        },
        "raster_sha256": live_sha,
        "validator_output": {
            "checks_passed": passed,
            "checks_total": len(checks),
            "all_passed": passed == len(checks),
            "whole_array_finite_in_0_1": checks["whole_array_finite_in_0_1"],
            "inside_unmasked_finite_in_0_1": checks["inside_unmasked_finite_in_0_1"],
            "outside_masked_or_nan": checks["outside_masked_or_nan"],
            "crs_shape_transform_match": checks["crs_match"] and checks["shape_match"]
            and checks["transform_match"],
            "status": f"{passed}/{len(checks)} PASS",
        },
        "submission_name": card["submission"]["name"],
        "submission_note_140": card["submission"]["note_140"],
        "note_length": len(card["submission"]["note_140"]),
        "verdict": card["verdict"],
        "ok_to_download_and_submit": card["ok_to_download_and_submit"],
        "n_dots": card["raster"]["n_dots"],
        "params": {
            "w_ridge": 0.5,
            "min_sep_px": 3,
            "collar_px": 4,
            "emission_cells": 1,
            "alpha": 0.2,
            "beta": 0.8,
            "kernel_radius_px": 3,
        },
        "generated_utc": card["generated_utc"],
        "files": {
            "primary_zeros_tif": f"docs/downloads/{zeros_tif.name}",
            "primary_zeros_sha256": live_sha,
            "primary_zeros_size_bytes": zeros_tif.stat().st_size,
            "primary_zeros_zip": f"docs/downloads/{zeros_zip.name}",
            "primary_zeros_zip_sha256": sha256(zeros_zip),
            "archive_nan_tif": f"docs/downloads/{nan_tif.name}",
            "archive_nan_sha256": nan["candidate_sha256"],
        },
        "score_evidence": {
            "label": "MODEL ESTIMATE — not organizer-confirmed",
            **card["score_estimate"],
        },
        "controlled_comparison": card.get("controlled_comparison"),
        "design_validation": card.get("design_validation"),
        "prior_independence": card.get("prior_independence"),
        "limitations": card["authorisation_limits"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(audit, indent=2))
    print(f"wrote {args.out}  ({audit['validator_output']['status']}, verdict={audit['verdict']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
