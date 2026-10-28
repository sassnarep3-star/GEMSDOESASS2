#!/usr/bin/env python3
"""Fail-closed local preflight for a DOE GEMS GeoTIFF candidate.

This command separates three claims that are often conflated:

* ``ok_to_download`` means the saved bytes pass the local GeoTIFF/range contract.
* ``unique_against_registry`` is copied only from an attached, machine-generated
  run card; this command does not pretend a partial registry is complete.
* ``ok_to_submit`` is true only when a run card explicitly records that decision.
  A format pass, a holdout score, or a projection never authorizes a weekly slot.

The output is JSON and the exit code is non-zero unless the explicit run-card
submission decision is true.  That is intentional: this tool is a safety gate,
not a way to turn a candidate into a submission by omission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

try:  # Works both as ``python scripts/submission_preflight.py`` and as a test import.
    from validate_tif import validate as validate_format
except ModuleNotFoundError:  # pragma: no cover - exercised by the direct CLI path
    from scripts.validate_tif import validate as validate_format


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _card_name(card: dict[str, Any]) -> str | None:
    submission = card.get("submission")
    if isinstance(submission, dict):
        return submission.get("name")
    return card.get("submission_name")


def _card_note(card: dict[str, Any]) -> str | None:
    submission = card.get("submission")
    if isinstance(submission, dict):
        return submission.get("note")
    return card.get("submission_note")


def _card_sha(card: dict[str, Any]) -> str | None:
    return card.get("raster_sha256") or card.get("files", {}).get("primary_zeros_tif_sha256")


def _card_zip_name(card: dict[str, Any]) -> str | None:
    if card.get("zip_filename"):
        return card["zip_filename"]
    if card.get("files", {}).get("primary_zeros_zip"):
        return Path(card["files"]["primary_zeros_zip"]).name
    return None


def _zip_contains_exactly(zip_path: Path, tif_name: str, tif_sha: str) -> tuple[bool, str]:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                return False, "zip CRC check failed"
            names = archive.namelist()
            if names != [tif_name]:
                return False, f"zip members are {names!r}, expected [{tif_name!r}]"
            if hashlib.sha256(archive.read(tif_name)).hexdigest() != tif_sha:
                return False, "zip TIFF bytes do not match candidate bytes"
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        return False, f"cannot inspect zip: {exc}"
    return True, "single TIFF member and byte hash match"


def preflight(candidate: Path, sample: Path, card_path: Path | None = None) -> dict[str, Any]:
    """Return a JSON-serializable preflight receipt without mutating the candidate."""
    format_receipt = validate_format(candidate, sample)
    candidate_sha = sha256_file(candidate)
    card: dict[str, Any] = {}
    card_errors: list[str] = []
    if card_path is not None:
        try:
            card = json.loads(card_path.read_text(encoding="utf-8"))
            if not isinstance(card, dict):
                raise ValueError("run card root is not an object")
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            card_errors.append(f"run card unavailable or invalid: {exc}")

    expected_sha = _card_sha(card)
    if expected_sha and candidate_sha != expected_sha:
        card_errors.append(f"candidate SHA-256 {candidate_sha} != run-card SHA-256 {expected_sha}")

    note = _card_note(card)
    name = _card_name(card)
    if note is not None and not (1 <= len(note) <= 140):
        card_errors.append(f"submission note length is {len(note)}; expected 1..140")
    if name is not None and not name.strip():
        card_errors.append("submission name is empty")

    zip_receipt: dict[str, Any] | None = None
    expected_zip_name = _card_zip_name(card)
    if expected_zip_name:
        zip_path = candidate.parent / expected_zip_name
        if not zip_path.exists():
            card_errors.append(f"run-card zip is missing: {zip_path}")
        else:
            zip_ok, zip_reason = _zip_contains_exactly(zip_path, candidate.name, candidate_sha)
            zip_receipt = {
                "path": str(zip_path),
                "sha256": sha256_file(zip_path),
                "matches_candidate": zip_ok,
                "reason": zip_reason,
            }
            if not zip_ok:
                card_errors.append(zip_reason)

    format_ok = bool(format_receipt["strict_local_format_pass"])
    explicit_submit = card.get("ok_to_submit") is True
    # Some older cards put the decision under a nested submission object.  Do not
    # infer approval from ``verdict=promote`` alone because selector authorization
    # is deliberately a separate step in the standing protocol.
    if isinstance(card.get("submission"), dict):
        explicit_submit = explicit_submit or card["submission"].get("ok_to_submit") is True
    unique = card.get("scientific_and_genuine_uniqueness_gate") is True
    if not unique:
        unique = card.get("correlation_and_overlap_vs_registry", {}).get("all_uniqueness_gates_passed") is True
    ok_to_download = format_ok and not card_errors
    ok_to_submit = ok_to_download and explicit_submit and unique
    reasons = []
    if not format_ok:
        reasons.append("saved bytes fail the local GeoTIFF/range contract")
    if card_errors:
        reasons.extend(card_errors)
    if not explicit_submit:
        reasons.append("run card does not explicitly authorize submission")
    if not unique:
        reasons.append("run card does not establish a complete uniqueness gate")

    return {
        "candidate": candidate.name,
        "candidate_sha256": candidate_sha,
        "sample": str(sample),
        "run_card": str(card_path) if card_path else None,
        "validator": format_receipt,
        "submission_name": name,
        "submission_note": note,
        "zip": zip_receipt,
        "ok_to_download": ok_to_download,
        "ok_to_submit": ok_to_submit,
        "decision": "OK TO DOWNLOAD; DO NOT SUBMIT" if ok_to_download and not ok_to_submit else (
            "OK TO DOWNLOAD AND SUBMIT" if ok_to_submit else "DO NOT DOWNLOAD"
        ),
        "reasons": reasons,
        "organizer_accepted": None,
        "weekly_slot_spent": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--run-card", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if not args.candidate.exists():
        parser.error(f"candidate does not exist: {args.candidate}")
    if not args.sample.exists():
        parser.error(f"sample does not exist: {args.sample}")
    receipt = preflight(args.candidate, args.sample, args.run_card)
    text = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.out.with_suffix(args.out.suffix + ".partial")
        try:
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(args.out)
        finally:
            temporary.unlink(missing_ok=True)
    print(text, end="")
    return 0 if receipt["ok_to_submit"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
