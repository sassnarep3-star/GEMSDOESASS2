"""Checks for the 2026-10-30 session: corrected verdict, measured receipts, and label discipline.

Every assertion reads a committed receipt or the saved raster bytes; nothing is asserted from
prose. The full-registry receipt is produced by scripts/focus_uniqueness_check.py over
scripts/fetch_gems_registry_full.py output (112 public GEMS-named repos).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
DOWNLOADS = ROOT / "docs" / "downloads"
CAND = DOWNLOADS / "gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
CAND_NAN = DOWNLOADS / "gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-nan.tif"


def test_run_card_is_negative_and_matches_saved_bytes() -> None:
    rc = json.loads((EVIDENCE / "unique_run_card_cc522684.json").read_text())
    assert rc["verdict"] == "negative"
    assert rc["ok_to_submit"] is False and rc["ok_to_download_and_submit"] is False
    assert rc["selector_approved"] is False
    digest = hashlib.sha256(CAND.read_bytes()).hexdigest()
    assert digest == rc["raster_sha256"]
    assert digest == rc["files"]["zeros"]["sha256"]
    assert len(rc["submission_note_140"]) <= 140
    # The downloadable twin must be byte-identical to the evidence card.
    twin = json.loads((DOWNLOADS / "gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-audit.json").read_text())
    assert twin == rc


def test_literal_lattice_gate_fails_for_the_candidate() -> None:
    rec = json.loads((EVIDENCE / "lattice_gate_recheck_20261030.json").read_text())
    cand = next(c for c in rec["candidates"] if c["file"].endswith("-zeros.tif"))
    assert cand["literal_lattice_gate_pass"] is False
    assert cand["overlap_vs_lattice_3px"] > 0.7
    assert cand["dots"] == 22163
    # The rule can only be met from border cells; every far cell is near the edge.
    far = rec["footprint_cells_farther_than_3px_from_lattice"]
    assert far == 6649
    assert rec["far_cells_min_distance_to_footprint_edge_px"]["max"] <= 3.0
    assert cand["dots_needed_in_far_cells_to_pass"] == 6649


def test_focus_pairwise_matrix_matches_audit_pins() -> None:
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    matrix = json.loads((EVIDENCE / "focus_pairwise_matrix_20261030.json").read_text())
    for row in audit["historical_sites"]:
        summary = matrix["summary"][row["site"]]
        assert summary["sha256"] == row["sha256"], row["site"]
        assert summary["dots"] == row["dot_count"], row["site"]
        assert summary["literal_lattice_gate_70pct_pass"] is False
    assert matrix["lattice"]["sha256"] == audit["inputs"]["lattice"]["sha256"]
    cand = next(k for k in matrix["summary"] if k.startswith("gemsdoesass2"))
    assert matrix["summary"][cand]["overlap_vs_lattice_3px"] > 0.7


def test_lineage_subset_relations_are_recorded() -> None:
    matrix = json.loads((EVIDENCE / "focus_pairwise_matrix_20261030.json").read_text())
    subsets = matrix["exact_pixel_subset_relations"]
    assert "GEMSDOE32 subset_of GEMSDOE25" in subsets
    assert "GEMSDOE25 subset_of GEMSDOE30" in subsets and "GEMSDOE30 subset_of GEMSDOE25" in subsets
    assert subsets["GEMSDOE32 subset_of GEMSDOE25"]["dots"] == 37654


def test_validator_conventions_on_both_twins() -> None:
    from scripts.validate_tif import validate

    sample = ROOT / "data/bridge/sample_submission.tif"
    zeros = validate(CAND, sample)
    nan = validate(CAND_NAN, sample)
    assert zeros["strict_local_format_pass"] is True
    assert zeros["checks"]["whole_array_finite_in_0_1"] is True
    assert zeros["ok_to_submit"] is False  # format inspection never approves
    # IR-31-01: the old assertion here was `nan[...] is False`, which encoded an
    # over-narrow rule -- `all(checks.values())` demands BOTH outside-bounds checks at
    # once, and a file carrying finite values outside the footprint with no internal
    # mask can never satisfy `outside_masked_or_nan`, while a spec-compliant NaN-outside
    # file can never satisfy `whole_array_finite_in_0_1`. Only a masked-outside file
    # could ever pass. The fixed rule requires the structural checks, the
    # inside-footprint range check, and ONE valid outside-bounds encoding, and records
    # which encoding was used plus whether the portal's "[0,1]" check can fire.
    assert nan["strict_local_format_pass"] is True
    assert nan["outside_bounds_encoding"] != "INVALID"
    assert zeros["outside_bounds_encoding"] != "INVALID"
    assert zeros["portal_range_safe"] is True
    # The nan twin must reproduce the organizer template's NaN mask exactly.
    with rasterio.open(sample) as ds:
        ref = ds.read(1)
    with rasterio.open(CAND_NAN) as ds:
        a = ds.read(1)
    assert np.array_equal(np.isnan(a), np.isnan(ref))


def test_no_score_is_projected_anywhere() -> None:
    """Run cards must never carry an unlabelled number as a score estimate."""
    for path in EVIDENCE.glob("*.json"):
        data = json.loads(path.read_text())
        blob = json.dumps(data)
        assert "ORGANIZER-CONFIRMED" not in blob or "receipt" in blob.lower(), path.name
        if isinstance(data, dict) and "holdout_dti" in data:
            hd = data["holdout_dti"]
            if isinstance(hd, dict) and hd.get("dti") is not None:
                assert str(hd.get("label", "")).startswith("HOLDOUT-DTI"), path.name


def test_full_registry_receipt_covers_the_public_repos() -> None:
    path = EVIDENCE / "focus_uniqueness_full_registry_20261030.json"
    assert path.exists(), "run scripts/focus_uniqueness_check.py over the full registry first"
    data = json.loads(path.read_text())
    assert data["registry_unique_sha256_rasters"] >= 1000
    # Probes are classified by name AND by measured dot density (IR-30-10).
    assert "probe_density_fraction_excluded_from_genuine_gates" in data
    cand = next(c for c in data["candidates"] if c["candidate"].endswith("-zeros.tif"))
    # Literal gate must record the lattice failure.
    assert cand["literal_all_gates_pass"] is False
    assert cand["literal_worst_overlap_3px_all_rasters"] > 0.7
    # Dense masks/probability surfaces are reported as probes with a reason, not as genuine peers.
    for row in cand["space_filling_probe_overlaps"]:
        assert row["space_filling_probe"] is True and row["space_filling_reason"] in ("name", "density")
    for row in cand["closest_5_genuine"]:
        assert row["space_filling_probe"] is False
        assert row["registry_dots"] is not None
    # The candidate's own nan twin must be excluded as a self-comparison (content identity),
    # and the worst genuine third-party peer is GEMSDOE86 gmc-linepost at 98.41% (fails 70%).
    assert cand["self_twins_excluded"], "nan twin must be recorded as a self-twin"
    top = cand["closest_5_genuine"][0]
    assert top["overlap_3px"] == 0.984118 and "GEMSDOE86" in top["file"]
    assert cand["genuine_worst_overlap_3px"] == 0.984118
    # The genuine verdict must be the boolean combination of its own gates.
    gates_ok = (cand["genuine_worst_overlap_3px"] <= 0.70 and cand["genuine_worst_abs_spearman"] <= 0.90)
    assert cand["unique_by_protocol"] == gates_ok
    # Unreadable registry rasters are recorded, not crashed on (IR-30-05).
    assert isinstance(data.get("registry_unreadable"), list)
