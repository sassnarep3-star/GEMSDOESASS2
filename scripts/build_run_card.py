#!/usr/bin/env python3
"""Build this session's fail-closed card from measured audit receipts.

This deliberately cannot promote future candidates: it is a negative preflight,
not a selector, training pipeline, or substitute for the shared tools.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    upstream = json.loads((ROOT / "docs/data/upstream-check.json").read_text())
    if not audit["lattice"]["bound_at_37654"]["necessarily_exceeds_limit"]:
        raise ValueError("The pinned bound did not establish a stop; investigate rather than publish a stale card")
    if upstream["ready_for_shared_holdout"]:
        raise ValueError("Upstream probe result changed; review the entire decision before rebuilding")
    card = {
        "hypothesis": "Prospective H1: multi-sensor boundary stability under modality-specific perturbations; no method lane was assigned and this hypothesis was not tested.",
        "mechanism": "Anomaly edges stable under realistic perturbations across magnetic and gravity channels may indicate buried structure beneath cover; test only with a restored fold-safe feature cache.",
        "named_non_fault_process": "A persistent lithologic contact or dike swarm can produce similarly stable magnetic and gravity gradients.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI", "evaluator_version": None, "n_withheld_positives": None,
            "dti": None, "ci95": None,
            "status": "NOT RUN: no assigned method lane, no reusable cache or current same-protocol control; shared evaluator and surface gate fail synthetic probes.",
        },
        "correlation_overlap_vs_registry": {
            "new_surface_rank_correlation": None, "new_surface_overlap": None, "new_final_dot_overlap": None,
            "status": "No new surface or dots were created. The complete current registry was not checked.",
            "lattice_sha256": audit["inputs"]["lattice"]["sha256"],
            "historical_budget_bound": audit["lattice"]["bound_at_37654"],
            "existing_witnesses": [{"site": x["site"], "sha256": x["sha256"],
                                    "within_3px_fraction": x["fraction"],
                                    "fails_literal_rule": x["fails_literal_overlap_rule"]}
                                   for x in audit["existing_candidate_witnesses"]],
        },
        "raster_sha256": None,
        "validator_output": {
            "new_raster": None, "inside_nan": None, "inside_range_0_1": None,
            "crs_shape_transform_match": None,
            "status": "This audit generated no TIFF. Parallel-branch research files were inspected separately; see docs/data/format-parallel-*.json and research/parallel-integration.md.",
        },
        "submission_name": None,
        "note": "No assigned lane; uniqueness and shared-tool preflight failed. DO NOT SUBMIT.",
        "verdict": "negative", "ok_to_submit": False,
        "selector_approved": False,
        "scope": "This independent audit session only; other merged branches reported separate experiments and produced research TIFFs.",
        "new_experiments": audit["new_experiments"], "weekly_slots_spent": audit["weekly_slots_spent"],
        "blockers": [
            "No single geological method lane was supplied for this parallel session.",
            "Reusable prepared features, frozen comparator, and the complete current registry are absent from this checkout.",
            "At the usual 37,654-dot budget the literal all-entry lattice rule forces overlap above 70%.",
            "Two upstream shared-tool synthetic checks fail; upstream is read-only and existing issues are open.",
            "Official sample and current account quota/receipt are inaccessible without DrivenData authorization.",
        ],
        "audit_receipt": "docs/data/audit.json", "shared_tool_receipt": "docs/data/upstream-check.json",
    }
    if len(card["note"]) > 140:
        raise ValueError("Run-card note is too long")
    target = ROOT / "docs/data/run-card.json"
    target.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {target}; verdict={card['verdict']}; no file approved")


if __name__ == "__main__":
    main()
