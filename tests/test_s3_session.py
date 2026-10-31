"""Tests for the 2026-10-31 S3 session: shipped submission bytes, run card, ring prior.

These tests are data-independent except for files committed to the repository
(data/bridge/*, docs/downloads/*, evidence/*), so they run on a clean machine.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

RUN_CARD = ROOT / "evidence" / "s3_run_card_20261031.json"
VALIDATOR_RECEIPTS = ROOT / "evidence" / "s3_validator_receipts_20261031.json"
UNI = ROOT / "evidence" / "s3_uniqueness_20261031.json"
UNI24 = ROOT / "evidence" / "s3_uniqueness_24000_20261031.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def run_card() -> dict:
    return json.loads(RUN_CARD.read_text())


def test_run_card_exists_and_verdict(run_card):
    assert run_card["verdict"] == "promote"
    assert run_card["weekly_slots_spent"] == 0
    assert run_card["score_estimate"]["headline"] == 0.29
    assert run_card["score_estimate"]["label"].startswith("MODEL ESTIMATE")


def test_run_card_note_lengths(run_card):
    for key in ("primary", "alternate_n_axis_probe"):
        note = run_card["raster"][key]["note_140char"]
        assert len(note) <= 140, f"{key} note is {len(note)} chars"


def test_primary_raster_hash_matches_bytes(run_card):
    path = ROOT / "docs" / "downloads" / f"{run_card['raster']['primary']['stem']}-zeros.tif"
    assert path.exists()
    assert _sha256(path) == run_card["raster"]["primary"]["sha256_zeros"]


def test_primary_raster_passes_13_check_validator(run_card):
    from gems_sass2.submission import validate_geotiff

    path = ROOT / "docs" / "downloads" / f"{run_card['raster']['primary']['stem']}-zeros.tif"
    v = validate_geotiff(
        str(path),
        str(ROOT / "data" / "bridge" / "sample_submission.tif"),
        str(ROOT / "data" / "bridge" / "labels.tif"),
        strict_all_finite=True,
    )
    assert v["all_passed"], v["checks"]
    assert v["checks_passed"] == 13
    assert v["max_in_footprint"] <= 1.0 and v["min_in_footprint"] >= 0.0
    assert v["all_12279160_finite"] is True
    assert v["positive_on_catalogue"] == 0


def test_uniqueness_receipts_pass_genuine_peer_gate():
    for path in (UNI, UNI24):
        d = json.loads(path.read_text())
        peers = [r for r in d["top_overlaps"] if "r13-lattice" not in r["ref"]]
        worst = max(peers, key=lambda r: r["overlap_3px_pct"])
        assert worst["overlap_3px_pct"] <= 70.0, (path, worst)
        assert max(r["abs_spearman"] for r in peers) <= 0.90
        # literal clause failure is against the calibration probe only (IR-S3-6)
        probe = [r for r in d["top_overlaps"] if "r13-lattice" in r["ref"]]
        assert probe and probe[0]["overlap_3px_pct"] > 70.0


def test_ring_field_profile():
    from exp_thermal_conduit import COLLAR_PX, ring_field

    labels = np.zeros((200, 200), dtype=bool)
    labels[100, 100] = True  # one catalogue cell
    m = ring_field(labels)
    # zero inside/around the collar
    assert m[100, 100] == 0.0
    assert m[100, 102] == 0.0  # 2 px away < 3 px collar
    # ring peak near 12 px
    assert m[100, 112] > m[100, 130] > m[100, 190]
    # uniform floor 0.20 far away
    assert abs(float(m[100, 190]) - 0.20) < 0.01
    assert float(m[100, 112]) > 0.9


def test_rank01_preserves_shape():
    from exp_thermal_conduit import rank01

    a = np.random.default_rng(0).random((7, 9))
    r = rank01(a)
    assert r.shape == a.shape
    assert 0.0 <= float(r.min()) and float(r.max()) <= 1.0


def test_exp2_receipts_cover_pre_registered_configs():
    d = json.loads((ROOT / "evidence" / "exp2_placement_decision.json").read_text())
    names = {r["name"] for r in d["rows"]}
    assert names == {"uniform-binary-37654", "ring-binary-37654",
                     "ring-binary-24000", "ring-plateau1-37654"}
    by = {r["name"]: r for r in d["rows"]}
    assert by["ring-binary-37654"]["ihr_pooled_dti"] > by["uniform-binary-37654"]["ihr_pooled_dti"]


def test_executive_summary_and_howto_exist():
    for rel in ("docs/executive-summary.md", "docs/executive-summary.html",
                "docs/how-to-submit.html", "research/2026-10-31-hypotheses-s3.md"):
        assert (ROOT / rel).exists(), rel
