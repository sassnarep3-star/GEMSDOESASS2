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
    """Exactly one candidate is advertised (strainridge: format + genuine-peer lane gate pass).
    The lattice clause fails for it (99.89%) exactly as it fails for every interior placement,
    and both pages must disclose that failing clause instead of hiding it."""
    import hashlib

    rc = json.loads((ROOT / "evidence/unique_run_card_cc522684.json").read_text())
    assert rc["verdict"] == "negative"
    assert rc["ok_to_submit"] is False and rc["ok_to_download_and_submit"] is False
    assert rc["correlation_overlap_vs_registry"]["passes_literal_lattice_gate"] is False
    recheck = json.loads((ROOT / "evidence/lattice_gate_recheck_20261030.json").read_text())
    cand = next(c for c in recheck["candidates"] if c["file"].endswith("-zeros.tif"))
    assert cand["literal_lattice_gate_pass"] is False and cand["overlap_vs_lattice_3px"] > 0.7
    tif = DOCS / "downloads" / cand["file"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == cand["sha256"] == rc["raster_sha256"]

    # The one promoted submission run card (separate from the negative research cards)
    run_card = None
    for p in DOCS.glob("downloads/*-audit.json"):
        c = json.loads(p.read_text())
        if c.get("verdict") == "promote" and c.get("ok_to_download_and_submit"):
            run_card = c
            break
    assert run_card is not None, "No promoted unique submission run card found"
    assert run_card["n_dots"] == 37654
    assert run_card["validator_output"]["all_passed"] is True
    assert run_card["correlation_overlap_vs_registry"]["passes_lane"] is True
    assert len(run_card["submission_note_140"]) <= 140
    # Its bytes must be the advertised bytes.
    promoted_tif = DOCS / "downloads" / "gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif"
    assert hashlib.sha256(promoted_tif.read_bytes()).hexdigest() == run_card["raster_sha256"]

    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "ok to download and submit" in page.lower()
        assert "lattice" in page.lower(), "the failing lattice clause must be disclosed"
        assert "localhost" not in page and "127.0.0.1" not in page
    assert "99.89" in exec_html
    assert "MODEL ESTIMATE" in exec_html
    assert "not an organizer score" in exec_html.lower() or "NOT organizer-confirmed" in exec_html
    assert "gemsass2-s3-ring-binary-37654-20261031T054926Z" in exec_html
    assert "downloads/gemsass2-s3-ring-binary-37654-20261031T054926Z-zeros.tif" in index
    # Research artifacts remain marked research only
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
