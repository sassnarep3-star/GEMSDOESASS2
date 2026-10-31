"""Automated verification of GitHub Pages HTML/assets, local links, copyable metadata, and README."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_github_pages_files_and_local_links_exist() -> None:
    assert (DOCS / ".nojekyll").exists()
    html_pages = [
        DOCS / "index.html",
        DOCS / "executive-summary.html",
        DOCS / "hvfd-exp3.html",
        DOCS / "hvfd-forensics.html",
    ]
    for page in html_pages:
        assert page.exists(), f"Missing page: {page}"
        text = page.read_text(encoding="utf-8")
        assert "localhost" not in text
        assert "127.0.0.1" not in text
        for attr_val in re.findall(r'(?:href|src)="([^"]+)"', text):
            if attr_val.startswith(("http://", "https://", "#", "mailto:", "${")):
                continue
            clean = attr_val.split("#")[0].split("?")[0]
            if not clean:
                continue
            target = (page.parent / clean).resolve()
            assert target.exists(), f"Broken relative asset/link '{attr_val}' in {page.name} -> {target}"
            if target.is_file():
                assert target.stat().st_size > 0, f"Empty asset '{attr_val}' in {page.name}"


def test_one_promoted_candidate_and_honest_gate_disclosure() -> None:
    """Exactly one candidate is advertised, and the 2026-10-31 promotion is pinned.

    The earlier strain-ridge card is retained as history but is no longer promoted: the
    independent-target experiment reversed its ranking (see evidence/emission_controls.json).
    The promoted artifact must match its audit receipt byte-for-byte, and both pages must
    disclose the caveats that actually bound the claim.
    """
    import hashlib

    rc = json.loads((ROOT / "evidence/unique_run_card_cc522684.json").read_text())
    assert rc["verdict"] == "negative"
    assert rc["ok_to_submit"] is False and rc["ok_to_download_and_submit"] is False
    assert rc["correlation_overlap_vs_registry"]["passes_literal_lattice_gate"] is False

    promoted = "gemsass2-slopetilt-300k-20261031-zeros.tif"
    audit = json.loads((DOCS / "downloads" / "gemsass2-slopetilt-300k-20261031-audit.json").read_text())
    assert audit["verdict"] == "promote" and audit["ok_to_download_and_submit"] is True
    assert audit["validator_output"]["all_passed"] is True
    assert audit["correlation_overlap_vs_registry"]["passes_lane"] is True
    assert audit["correlation_overlap_vs_registry"]["max_pct_within_3px_of_one_registry"] < 70.0
    assert audit["correlation_overlap_vs_registry"]["max_abs_spearman"] < 0.90
    assert len(audit["submission_note_140"]) <= 140
    assert audit["independent_target"]["DTI"] > audit["controls"]["space_filling_same_budget"]
    assert audit["independent_target"]["DTI"] > audit["controls"]["fitted_125_feature_model"]

    tif = DOCS / "downloads" / promoted
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == audit["raster_sha256"]

    # the run card behind it must agree on the same bytes and the same gate
    card = json.loads((ROOT / "evidence" / "final_run_card.json").read_text())
    assert card["sha256"] == audit["raster_sha256"]
    assert card["n_cells"] == audit["n_dots"]
    assert card["uniqueness"]["gate"]["passes"] is True

    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "ok to download and submit" in page.lower()
        assert "localhost" not in page and "127.0.0.1" not in page
        # the caveats that bound the claim must be present, not hidden
        assert "MODEL ESTIMATE" in page or "model estimate" in page
    assert promoted in index and promoted in exec_html
    assert "0.403" in exec_html and "0.295" in exec_html and "0.192" in exec_html
    assert "0.277" in exec_html, "the law-consistent tie must be disclosed"
    assert "terrain" in exec_html.lower()
    assert "no organizer" in exec_html.lower() or "no organizer" in index.lower()
    artifacts = (DOCS / "hvfd-exp3.html").read_text()
    assert "Research only" in artifacts and "DO NOT SUBMIT" in artifacts


def test_nine_focus_sites_and_readme_links() -> None:
    exec_html = (DOCS / "executive-summary.html").read_text()
    readme = (ROOT / "README.md").read_text()
    audit = json.loads((DOCS / "data/audit.json").read_text())
    for row in audit["historical_sites"]:
        assert row["site"] in exec_html
        assert f'{row["reported"]:.4f}' in exec_html
        assert row["artifact_url"] in exec_html
    assert "USER-REPORTED" in exec_html
    assert "MODEL ESTIMATE" in exec_html
    for md_link in re.findall(r"\]\(([^)]+)\)", readme):
        if md_link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = md_link.split("#")[0].strip()
        if clean:
            assert (ROOT / clean).resolve().exists(), f"Broken README link: {md_link}"
