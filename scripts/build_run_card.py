#!/usr/bin/env python3
"""Build this session's negative run card from measured receipts.

This is deliberately not a selector or candidate generator. If the evidence
changes, fail closed and require a fresh review instead of publishing stale claims.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_card(audit: dict, upstream: dict, restoration: dict) -> dict:
    if not audit["lattice"]["bound_at_37654"]["necessarily_exceeds_limit"]:
        raise ValueError("Pinned lattice bound no longer establishes a stop; review before rebuilding")
    if upstream["ready_for_shared_holdout"]:
        raise ValueError("Upstream probe result changed; review the entire decision before rebuilding")
    if audit["new_experiments"] != 0 or audit["new_tiff_created"] or audit["weekly_slots_spent"] != 0:
        raise ValueError("Session scope changed; the negative-only card builder is no longer applicable")
    witnesses = {item["id"]: item for item in audit["existing_candidate_witnesses"]}
    def summarize(id_: str) -> dict:
        w = witnesses[id_]
        if not w["fails_literal_overlap_rule"] or w["fraction"] <= 0.70:
            raise ValueError(f"Prior artifact {id_} no longer establishes a stop")
        return {"sha256": w["sha256"], "dots": w["candidate_dots"],
                "within_3px": w["dots_within_3px"], "fraction": w["fraction"], "duplicate_stop": True}
    if restoration["bands"] != 19:
        raise ValueError("Feature restoration evidence changed; review before rebuilding")
    card = {
        "hypothesis": "Within the previously described XGHF family, magnetic and gravity boundaries that remain aligned under scale and modality perturbations may better identify buried faults. This proposal is not an assigned lane and has not been tested.",
        "mechanism": "Compare multiscale, cross-gradient boundary stability using the restored owner-mirror competition features; any catalogue-derived field must use only fold-visible faults.",
        "named_non_fault_process": "Lithologic contacts and dike swarms can produce similarly stable magnetic and gravity boundaries.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI", "evaluator_version": None, "withheld_positive_pixels": None,
            "dti": None, "ci95": None,
            "status": "NOT RUN: literal duplicate budget stop and unresolved shared-tool defects; no qualified comparable baseline.",
        },
        "leakage_canary": {"status": "NOT RUN: no feature or geological experiment executed in this session.", "max_auc": None},
        "correlation_overlap_vs_registry": {
            "new_surface_spearman": None, "new_surface_preview_overlap": None, "new_final_dot_overlap": None,
            "status": "No new surface or dots produced. Full current registry and surfaces unavailable.",
            "lattice_reference_sha256": audit["inputs"]["lattice"]["sha256"],
            "previous_hvfd": summarize("parallel_hvfd_zeros"),
            "previous_xghf": summarize("parallel_xghf_zeros"),
            "bound_at_37654": audit["lattice"]["bound_at_37654"],
        },
        "raster_sha256": None,
        "validator_output": {
            "new_raster": None, "inside_nan": None, "inside_range_0_1": None, "crs_shape_transform_match": None,
            "status": "No new raster generated. Previously inspected TIFFs pass local format checks only; no organizer receipt.",
        },
        "submission_name": None,
        "note": "No qualifying new file. Duplicate and shared-tool stops apply; DO NOT SUBMIT.",
        "verdict": "negative", "ok_to_submit": False, "selector_approved": False,
        "new_experiments": audit["new_experiments"], "weekly_slots_spent": audit["weekly_slots_spent"],
        "cache_provenance": "19-band owner mirror restored and SHA-pinned locally; ignored cache is not an authenticated organizer download.",
        "blockers": [
            "User prompt supplies no single explicit lane paragraph; repo lane is a prior proposal.",
            "The literal lattice stop is unavoidable at 37,654 distinct dots.",
            "Shared GEMSDOE32 evaluator and pre-placement gate still fail synthetic probes; upstream issues are open.",
            "Current complete registry, fold-local comparator, authenticated organizer sample, and account quota are unavailable.",
        ],
        "audit_receipt": "docs/data/audit.json", "shared_tool_receipt": "docs/data/upstream-check.json",
        "data_receipt": "evidence/data_restoration_20261028.json",
    }
    if len(card["note"]) > 140:
        raise ValueError("Run-card note is too long")
    return card


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent,
                                     prefix=f".{path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(text)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    upstream = json.loads((ROOT / "docs/data/upstream-check.json").read_text())
    restoration = json.loads((ROOT / "evidence/data_restoration_20261028.json").read_text())
    card = build_card(audit, upstream, restoration)
    text = json.dumps(card, indent=2, allow_nan=False) + "\n"
    for name in ("run-card.json", "latest-run-card.json"):
        write_atomic(ROOT / "docs/data" / name, text)
    print("Wrote negative run cards; no file approved.")


if __name__ == "__main__":
    main()
