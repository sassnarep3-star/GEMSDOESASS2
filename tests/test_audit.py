import json
from fractions import Fraction
from pathlib import Path

import pytest

from scripts.audit_snapshot import fetch_pinned, forced_overlap

ROOT = Path(__file__).resolve().parents[1]


def test_strict_threshold_and_pigeonhole():
    at_boundary = forced_overlap(3, 10)
    assert at_boundary["minimum_overlap_fraction"] == .7
    assert not at_boundary["necessarily_exceeds_limit"]
    assert at_boundary["first_failing_dot_count"] == 11
    assert forced_overlap(3, 11)["necessarily_exceeds_limit"]
    assert forced_overlap(6649, 37654)["minimum_overlapping_dots"] == 31005
    assert forced_overlap(6649, 37654)["first_failing_dot_count"] == 22164
    assert forced_overlap(50, 2)["minimum_overlap_fraction"] == 0
    assert forced_overlap(0, 1, Fraction(7, 10))["necessarily_exceeds_limit"]
    with pytest.raises(ValueError): forced_overlap(3, 11, footprint_pixels=10)
    with pytest.raises(ValueError): forced_overlap(11, 3, footprint_pixels=10)


@pytest.mark.parametrize("outside,dots", [(-1, 5), (1, 0), (2, -1)])
def test_bound_rejects_invalid(outside, dots):
    with pytest.raises(ValueError): forced_overlap(outside, dots)


def test_fetch_no_cache_or_hash_mismatch_fails_closed(tmp_path):
    path = tmp_path / "asset.tif"; path.write_bytes(b"not the pinned bytes")
    with pytest.raises(ValueError): fetch_pinned({"sha256": "0" * 64}, path, False)


def test_snapshot_has_directional_evidence_and_no_fabricated_result():
    x = json.loads((ROOT / "docs/data/audit.json").read_text())
    c = json.loads((ROOT / "docs/data/run-card.json").read_text())
    assert len(x["historical_sites"]) == 9
    assert len(x["directional_overlap"]) == 72
    assert all(v["fraction"] > .7 for v in x["directional_overlap"].values())
    assert all(not s["unique_against_nine_under_dot_rule"] for s in x["historical_sites"])
    assert x["lineage_analysis"]["GEMSDOE25_vs_GEMSDOE30_xor_pixels"] == 0
    assert x["lineage_analysis"]["GEMSDOE32_vs_GEMSDOE25_pruned_within_2px_xor_pixels"] == 0
    assert all(w["fails_literal_overlap_rule"] for w in x["existing_candidate_witnesses"])
    assert x["new_experiments"] == 0 and not x["new_tiff_created"]
    assert c["verdict"] == "negative" and c["ok_to_submit"] is False
    assert c["holdout_dti"]["dti"] is None and c["raster_sha256"] is None
    assert len(c["note"]) <= 140


def test_upstream_issue_is_not_silently_promoted():
    result = json.loads((ROOT / "docs/data/upstream-check.json").read_text())
    assert result["surface_duplicate"]["correct"] is False
    assert result["zero_truth_false_positive_accounting"]["correct"] is False
    assert result["ready_for_shared_holdout"] is False


def test_user_ledger_keeps_nine_supplied_claims_unverified():
    import csv
    from decimal import Decimal
    rows = list(csv.DictReader((ROOT / 'docs/data/user-reported-ledger.csv').open(newline='')))
    assert all(r['evidence_class'] == 'USER-REPORTED / UNVERIFIED' for r in rows)
    assert {r['site'] for r in rows if not r['value_as_supplied']} == {'GEMSDOE86', 'GEMSDOE88', 'GEMSDOE91'}
    sources = json.loads((ROOT / 'research/priority_sources.json').read_text())
    for site in sources['sites']:
        matches = [r for r in rows if r['site'] == site['site'] and r['submission_identifier_as_supplied'] == site['reported_id']]
        assert len(matches) == 1
        assert Decimal(matches[0]['value_as_supplied']) == Decimal(str(site['reported']))
