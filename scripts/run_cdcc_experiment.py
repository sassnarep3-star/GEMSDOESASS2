#!/usr/bin/env python3
"""Run one preregistered CDCC experiment and fail closed before any upload.

This runner has no DrivenData upload code.  It checks canaries, nine-site
novelty before/after placement, a spatial whole-segment proxy holdout, strict
GeoTIFF format, and input integrity.  A valid TIFF can still be marked
``DO_NOT_SUBMIT`` when a scientific/provenance gate is unmet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.candidate import CDCCInputs, HYPOTHESIS_ID, HYPOTHESIS_NAME, load_cdcc_inputs  # noqa: E402
from gemsdoesass2.holdout import (  # noqa: E402
    EVALUATOR_VERSION,
    evaluate_surface,
    leakage_canary,
    make_segment_holdout,
    paired_holdout_delta,
    select_top_local_maxima,
    strip_internal_arrays,
)
from gemsdoesass2.integrity import inspect_template_label_relationship  # noqa: E402
from gemsdoesass2.io import assert_same_grid, content_id, sha256_file, template_footprint  # noqa: E402
from gemsdoesass2.registry import audit_final_dots, audit_surface  # noqa: E402
from gemsdoesass2.submission import (  # noqa: E402
    make_submission_note,
    validate_submission,
    write_portal_safe_submission,
    write_single_tif_zip,
)

DEFAULT_BUDGET = 37_654


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")


def _label_array(labels_path: Path, template_path: Path) -> np.ndarray:
    assert_same_grid(template_path, labels_path, left_name="template", right_name="labels")
    with rasterio.open(labels_path) as source:
        if source.count != 1:
            raise ValueError("Labels/catalogue raster must be single-band")
        return source.read(1) > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True, help="Public known-fault catalogue proxy, not hidden organizer truth")
    parser.add_argument("--extensions", type=Path, required=True, help="GeoDAWN extensions stack; band 4 is TMI up150")
    parser.add_argument("--radiometric", type=Path, required=True, help="GeoDAWN radiometric stack; band 3 is U/Th")
    parser.add_argument("--registry-manifest", type=Path, default=ROOT / "registry" / "focus_registry.json")
    parser.add_argument("--registry-dir", type=Path, default=ROOT / "data" / "registry_rasters")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "cdcc")
    parser.add_argument("--date", default="20261027", help="UTC date stamp used in output names")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--input-provenance", choices=("peer_mirror_unverified", "organizer_authenticated_local"), default="peer_mirror_unverified")
    parser.add_argument("--bootstrap-draws", type=int, default=2_000)
    args = parser.parse_args()
    if args.budget <= 0 or args.bootstrap_draws < 100:
        raise SystemExit("budget must be positive and bootstrap-draws must be at least 100")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    footprint, _, grid = template_footprint(args.template)
    labels = _label_array(args.labels, args.template) & footprint
    integrity = inspect_template_label_relationship(args.template, args.labels)

    # ---- Experiment 1 / 3: fixed CDCC hypothesis, no parameter sweep. ----
    surface, features, support, source_provenance = load_cdcc_inputs(
        CDCCInputs(args.template, args.extensions, args.radiometric)
    )
    canary = leakage_canary(
        make_segment_holdout(footprint, labels, buffer_px=3),
        features,
        threshold=0.90,
    )

    # Required lane check 1: evaluate surface correlation before any dot placement.
    surface_novelty = audit_surface(
        surface,
        template_path=args.template,
        manifest_path=args.registry_manifest,
        registry_dir=args.registry_dir,
    )
    base_card: dict[str, Any] = {
        "schema": "gemsdoesass2-run-card-v1",
        "hypothesis": {
            "id": HYPOTHESIS_ID,
            "statement": "Uncatalogued faults may coincide with both TMI-up150 and U/Th contact edges.",
            "mechanism": "Cross-domain gradient concordance is used as a static structural-boundary proxy; no catalogue or registry raster enters the surface.",
            "non_fault_process_that_can_mimic_it": "Lithologic contacts, intrusive margins, acquisition/processing seams, and alteration fronts can co-locate magnetic and radiometric gradients without a fault.",
        },
        "protocol": {
            "experiment_number": 1,
            "maximum_experiments": 3,
            "submission_slot_spent": False,
            "evaluator_version": EVALUATOR_VERSION,
            "holdout": "whole 8-connected public-catalogue segments, quadrant blocks, 3-pixel buffer, visible faults masked pixel-exactly",
            "metric": "pooled DTI alpha=0.2 beta=0.8 300m triangular kernel",
            "budget_dots": args.budget,
        },
        "input_provenance": {
            "declared_status": args.input_provenance,
            "source": source_provenance,
            "template_label_integrity": integrity,
            "promotion_gate_pass": args.input_provenance == "organizer_authenticated_local" and integrity["promotion_gate_pass"],
        },
        "leakage_canary": canary,
        "surface_novelty": surface_novelty,
    }
    if not canary["pass"] or not surface_novelty["pass"]:
        base_card.update(
            {
                "raster_sha256": None,
                "validator_output": None,
                "submission": None,
                "verdict": "negative",
                "ok_to_download_for_research": False,
                "ok_to_submit": False,
                "stopped_reason": "leakage_canary" if not canary["pass"] else "duplicate_surface_or_incomplete_registry",
            }
        )
        _save_json(args.output_dir / f"{HYPOTHESIS_ID.lower()}-{args.date}-run-card.json", base_card)
        print(json.dumps(_json_safe(base_card), indent=2, sort_keys=True))
        return 2

    # Holdout is evaluated only after canary/surface gates.  The two individual
    # sensor surfaces are predeclared feature-alone controls, not tuned variants.
    holdout = make_segment_holdout(footprint, labels, buffer_px=3)
    arm_results = {
        "magnetic_edge_control": evaluate_surface(
            holdout, features["magnetic_up150_edge"], pixel_size_m=abs(grid.transform.a), budget=args.budget, n_bootstraps=args.bootstrap_draws
        ),
        "radiometric_edge_control": evaluate_surface(
            holdout, features["radiometric_u_th_edge"], pixel_size_m=abs(grid.transform.a), budget=args.budget, n_bootstraps=args.bootstrap_draws
        ),
        "cdcc_consensus": evaluate_surface(
            holdout, surface, pixel_size_m=abs(grid.transform.a), budget=args.budget, n_bootstraps=args.bootstrap_draws
        ),
    }
    control_name = max(
        ("magnetic_edge_control", "radiometric_edge_control"),
        key=lambda name: float(arm_results[name]["pooled_dti"]),
    )
    paired = paired_holdout_delta(
        arm_results["cdcc_consensus"], arm_results[control_name], n_bootstraps=args.bootstrap_draws
    )
    holdout_gate = {
        "candidate_point_beats_best_feature_alone_control": bool(
            arm_results["cdcc_consensus"]["pooled_dti"] > arm_results[control_name]["pooled_dti"]
        ),
        "paired_ci95_lower_bound_above_zero": paired["ci95_low"] > 0.0,
        "selected_control": control_name,
        "paired_delta": paired,
        "pass": False,  # set immediately below to make JSON evidence explicit
    }
    holdout_gate["pass"] = bool(
        holdout_gate["candidate_point_beats_best_feature_alone_control"]
        and holdout_gate["paired_ci95_lower_bound_above_zero"]
    )

    # Required lane check 2: create final dots only after the surface check, then
    # audit dots in memory before serializing a downloadable TIFF.
    final_eligible = footprint & support & ~labels
    final_dots = select_top_local_maxima(surface, final_eligible, budget=args.budget, nms_size=3)
    prediction = np.zeros(footprint.shape, dtype=np.float32)
    prediction[final_dots] = 1.0
    final_novelty = audit_final_dots(
        prediction,
        template_path=args.template,
        manifest_path=args.registry_manifest,
        registry_dir=args.registry_dir,
    )
    if not final_novelty["pass"]:
        base_card.update(
            {
                "holdout": {name: strip_internal_arrays(report) for name, report in arm_results.items()},
                "holdout_gate": holdout_gate,
                "final_dot_novelty": final_novelty,
                "raster_sha256": None,
                "validator_output": None,
                "submission": None,
                "verdict": "negative",
                "ok_to_download_for_research": False,
                "ok_to_submit": False,
                "stopped_reason": "duplicate_final_dots_or_incomplete_registry",
            }
        )
        _save_json(args.output_dir / f"{HYPOTHESIS_ID.lower()}-{args.date}-run-card.json", base_card)
        print(json.dumps(_json_safe(base_card), indent=2, sort_keys=True))
        return 2

    cid = content_id(prediction)
    # The builder is an experiment runner, not a weekly-slot selector.  Every
    # artifact it writes is visibly quarantined even if its format validates.
    filename = f"gemsdoesass2-cdcc-geodawn-contact-concordance-{args.date}-{cid}-RESEARCH-DO-NOT-SUBMIT-zeros.tif"
    output_tif = args.output_dir / filename
    write_portal_safe_submission(prediction, args.template, output_tif)
    validator = validate_submission(output_tif, args.template)
    if not validator["format_valid"]:
        raise RuntimeError("Strict writer emitted a TIFF that failed its own validator")
    output_zip = write_single_tif_zip(output_tif)
    note = make_submission_note(
        HYPOTHESIS_ID,
        "GeoDAWN magnetic-U/Th edge concordance; research only, no slot",
        cid,
    )

    all_gates = {
        "leakage_canary": bool(canary["pass"]),
        "surface_novelty": bool(surface_novelty["pass"]),
        "final_dot_novelty": bool(final_novelty["pass"]),
        "holdout_promotion": bool(holdout_gate["pass"]),
        "input_provenance_and_integrity": bool(base_card["input_provenance"]["promotion_gate_pass"]),
        "portal_safe_format": bool(validator["format_valid"]),
    }
    approved = all(all_gates.values())
    verdict = "promote" if approved else "negative"
    base_card.update(
        {
            "holdout": {name: strip_internal_arrays(report) for name, report in arm_results.items()},
            "holdout_dti": strip_internal_arrays(arm_results["cdcc_consensus"]),
            "holdout_gate": holdout_gate,
            "final_dot_novelty": final_novelty,
            "correlation_overlap_vs_registry": {
                "surface_max_abs_rank_correlation": surface_novelty["max_abs_rank_correlation"],
                "final_dot_max_directed_overlap_within_3px": final_novelty["max_directed_dot_overlap_within_3px"],
                "surface_pass": surface_novelty["pass"],
                "final_dot_pass": final_novelty["pass"],
            },
            "raster_sha256": sha256_file(output_tif),
            "validator_output": validator,
            "submission": {
                "file": output_tif.name,
                "zip": output_zip.name,
                "note": note,
                "note_characters": len(note),
                "dot_count": int(final_dots.sum()),
                "format": "portal-safe all-finite [0,1] zero-outside GeoTIFF",
            },
            "gates": all_gates,
            "verdict": verdict,
            "ok_to_download_for_research": True,
            "ok_to_submit": approved,
            "submission_authorization": (
                "No: fail-closed research artifact; see failed gates." if not approved else "Yes: all local gates passed; weekly-slot selector remains separate."
            ),
        }
    )
    run_card = args.output_dir / output_tif.with_suffix(".run-card.json").name
    _save_json(run_card, base_card)
    print(json.dumps(_json_safe(base_card), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
