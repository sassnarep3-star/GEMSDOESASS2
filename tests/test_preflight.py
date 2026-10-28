from __future__ import annotations

import json
from pathlib import Path

from scripts.submission_preflight import preflight

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "docs" / "downloads" / "gemsdoesass2-hvfd-exp3-hydrocollinear-37654-20261027T120000Z-fc98343e-zeros.tif"
SAMPLE = ROOT / "data" / "bridge" / "sample_submission.tif"
CARD = ROOT / "evidence" / "hvfd_exp3_run_card.json"


def test_preflight_is_explicit_about_download_vs_submit() -> None:
    receipt = preflight(CANDIDATE, SAMPLE, CARD)
    assert receipt["validator"]["strict_local_format_pass"] is True
    assert receipt["ok_to_download"] is True
    # The historical card has no separate selector authorization.  A positive
    # holdout and format pass must not silently become a weekly submission.
    assert receipt["ok_to_submit"] is False
    assert receipt["decision"] == "OK TO DOWNLOAD; DO NOT SUBMIT"
    assert receipt["organizer_accepted"] is None
    assert receipt["weekly_slot_spent"] is False


def test_preflight_rejects_a_tampered_candidate_hash(tmp_path) -> None:
    card = json.loads(CARD.read_text(encoding="utf-8"))
    card["raster_sha256"] = "0" * 64
    card_path = tmp_path / "card.json"
    card_path.write_text(json.dumps(card), encoding="utf-8")
    receipt = preflight(CANDIDATE, SAMPLE, card_path)
    assert receipt["ok_to_download"] is False
    assert any("SHA-256" in reason for reason in receipt["reasons"])
