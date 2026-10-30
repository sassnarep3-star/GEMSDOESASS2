"""Receipt tests for the 2026-10-30 re-verification.

These read committed receipts only (no network). They lock in the measured facts that
decide the submission status, so a later edit cannot silently restore the old claim.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "docs/data/focus-sites-verified.json"
GATE = ROOT / "docs/data/gate-and-lineage-recheck.json"
CARD = ROOT / "evidence/unique_run_card_cc522684.json"
TIF = ROOT / "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
CAND = "gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif"
NINE = ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]


def test_nine_sites_match_pinned_hashes_and_user_scores_are_labelled() -> None:
    data = json.loads(VERIFIED.read_text())
    recs = {r["label"]: r for r in data["records"]}
    for site in NINE:
        r = recs[site]
        assert r["sha256_matches_pin"] is True, site
        assert r["user_reported_label"].startswith("USER-REPORTED"), site
    assert "USER-REPORTED" in data["scores_label"]


def test_no_focus_site_is_unique_among_the_nine() -> None:
    data = json.loads(VERIFIED.read_text())
    for site in NINE:
        peers = {k: v for k, v in data["pairwise"][site].items() if k in NINE and k != site}
        assert max(v["overlap_3px_of_A_dots"] for v in peers.values()) >= 0.70, site


def test_candidate_is_unique_by_measurement_except_lattice() -> None:
    data = json.loads(VERIFIED.read_text())
    row = data["pairwise"][CAND]
    others = {k: v for k, v in row.items() if not k.startswith("gemsdoesass2-sparse-blind")}
    assert max(v["overlap_3px_of_A_dots"] for v in others.values()) < 0.70
    assert max(v["abs_spearman"] for v in others.values()) < 0.90


def test_lattice_gate_fails_for_candidate_and_is_recorded() -> None:
    gate = json.loads(GATE.read_text())
    rows = {r["subject"]: r for r in gate["lattice_gate_rows"]}
    cand = rows[CAND]
    assert cand["dots"] == 22163
    assert cand["lattice_overlap_3px"] > 0.70
    assert cand["lattice_gate_pass_le_0_70"] is False
    assert gate["lattice_registry_raster"]["sha256_pin_matches"] is True
    assert gate["footprint_cells_uncovered_by_lattice_3px"] == 6649


def test_lineage_0_2778_is_pixel_exact_subset_of_gemsdoe25() -> None:
    gate = json.loads(GATE.read_text())
    lin = gate["lineage_0_2778"]
    assert lin["gemsdoe32_pixels_not_in_gemsdoe25"] == 0
    assert lin["removed_dots"] == 44090 - 37654 == 6436
    assert lin["removed_all_within_2px_of_catalogue"] is True
    assert lin["gemsdoe25_minus_catalogue_2px_equals_gemsdoe32"] is True
    assert gate["marginal_identity"]["violations"] == 0


def test_run_card_is_blocked_not_promoted() -> None:
    card = json.loads(CARD.read_text())
    assert card["verdict"] == "negative"
    assert card["status"] == "blocked-owner-ruling"
    assert card["ok_to_download_and_submit"] is False
    assert card["download_available"] is True
    assert card["correlation_overlap_vs_registry"]["passes_lane"] is False
    assert card["holdout_dti"]["dti"] is None  # no holdout score is invented
    assert card["reverification_2026-10-30"]["organizer_receipt"] is None


def test_download_hash_matches_card_and_has_no_nan_or_outside_values() -> None:
    import hashlib

    import numpy as np
    import rasterio

    card = json.loads(CARD.read_text())
    assert hashlib.sha256(TIF.read_bytes()).hexdigest() == card["files"]["zeros"]["sha256"]
    with rasterio.open(TIF) as src:
        a = src.read(1)
        assert src.dtypes[0] == "float32" and src.count == 1
        assert src.crs.to_epsg() == 32611 and src.res == (100.0, 100.0)
    assert np.isfinite(a).all()
    assert float(a.min()) >= 0.0 and float(a.max()) <= 1.0
