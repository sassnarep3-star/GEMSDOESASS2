"""Pin the lattice-saturation receipt so its conclusions cannot drift silently."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "evidence" / "lattice_saturation_check.json"


def load():
    return json.loads(RECEIPT.read_text())


def test_docs_copy_matches_evidence():
    assert (ROOT / "docs" / "data" / "lattice_saturation_check.json").read_text() == RECEIPT.read_text()


def test_every_top_site_file_fails_the_literal_rule():
    data = load()
    rows = data["historical_top_files"]
    assert len(rows) == 9
    assert {r["site"] for r in rows} == {
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    }
    assert all(r["fails_literal_70pct_rule"] for r in rows)
    assert all(r["fraction"] > 0.99 for r in rows)


def test_random_placements_also_fail_so_the_rule_is_not_discriminative():
    controls = load()["random_placement_controls"]
    assert controls and all(c["all_exceed_70pct"] for c in controls)


def test_lattice_geometry_and_no_candidate_created():
    data = load()
    assert data["lattice"]["positive_pixels"] == 206895
    assert data["footprint_pixels_uncovered"] == 6649
    assert data["new_tiff_created"] is False and data["weekly_slots_spent"] == 0


def test_receipt_hashes_match_pinned_audit_inputs():
    config = json.loads((ROOT / "research" / "priority_sources.json").read_text())
    by_site = {s["site"]: s["sha256"] for s in config["sites"] if "sha256" in s}
    for row in load()["historical_top_files"]:
        assert row["sha256"] == by_site[row["site"]]
