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


def test_unique_candidate_is_held_by_literal_lattice_gate() -> None:
    """The sparse candidate is format-valid and unique vs the focus sites, but it fails the literal
    70 % lattice rule (99.74 %). Every public page must say HOLD, never OK TO SUBMIT."""
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
    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "NOT CLEARED FOR SUBMISSION" in page
        assert "OK TO DOWNLOAD AND SUBMIT" not in page
        assert "OK to download and submit" not in page
    assert rc["raster_sha256"][:16] in exec_html
    assert "downloads/gemsdoesass2-sparse-blind-conduit-22163" in exec_html
    assert "99.74%" in exec_html and "99.74%" in index
    assert "localhost" not in index and "127.0.0.1" not in index
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
    assert "USER-REPORTED" in exec_html and "No file approved" in exec_html
    for md_link in re.findall(r"\]\(([^)]+)\)", readme):
        if md_link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = md_link.split("#")[0].strip()
        if clean:
            assert (ROOT / clean).resolve().exists(), f"Broken README link: {md_link}"
