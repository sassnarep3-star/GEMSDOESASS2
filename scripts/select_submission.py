#!/usr/bin/env python3
"""Independent fail-closed selector for a future weekly submission slot.

This script does not upload. It verifies that a completed experiment's run card
actually permits release, that the bytes match the recorded SHA-256, and that
the note is bounded. The checked-in CDCC run card must be rejected.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.io import sha256_file  # noqa: E402
from gemsdoesass2.submission import validate_submission  # noqa: E402

REQUIRED_GATES = (
    "leakage_canary",
    "surface_novelty",
    "final_dot_novelty",
    "holdout_promotion",
    "input_provenance_and_integrity",
    "portal_safe_format",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-card", type=Path, required=True)
    parser.add_argument("--tif", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--weekly-cap-confirmed", action="store_true", help="Explicitly attest that this separate selector is within the current official weekly cap")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    card = json.loads(args.run_card.read_text())
    gate_values = card.get("gates", {})
    checks = {
        "run_card_verdict_promote": card.get("verdict") == "promote",
        "run_card_ok_to_submit": card.get("ok_to_submit") is True,
        "all_required_gates_true": all(gate_values.get(name) is True for name in REQUIRED_GATES),
        "weekly_cap_explicitly_confirmed": args.weekly_cap_confirmed,
        "tif_exists": args.tif.is_file(),
        "name_not_quarantined": "RESEARCH-DO-NOT-SUBMIT" not in args.tif.name,
    }
    checks["sha256_matches_run_card"] = bool(
        checks["tif_exists"] and card.get("raster_sha256") == sha256_file(args.tif)
    )
    note = card.get("submission", {}).get("note", "") if isinstance(card.get("submission"), dict) else ""
    checks["note_nonempty_and_at_most_140_characters"] = bool(note and len(note) <= 140)
    validator = validate_submission(args.tif, args.template) if checks["tif_exists"] else None
    checks["strict_validator_pass"] = bool(validator and validator.get("format_valid"))
    selected = all(checks.values())
    result = {
        "selector": "gemsdoesass2-independent-slot-selector-v1",
        "selected": selected,
        "ok_to_upload": selected,
        "checks": checks,
        "file": args.tif.name,
        "sha256": sha256_file(args.tif) if checks["tif_exists"] else None,
        "note": note,
        "validator": validator,
        "message": (
            "All local release gates pass. Upload remains an authorized-account action; save the organizer receipt."
            if selected
            else "NOT SELECTED: this artifact must not be uploaded. See failed checks."
        ),
    }
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    return 0 if selected else 2


if __name__ == "__main__":
    raise SystemExit(main())
