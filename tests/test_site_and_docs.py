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


def test_unique_submission_is_advertised_with_validation() -> None:
    card = json.loads((DOCS / "data/run-card.json").read_text())
    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    # The unique submission run card (separate from the legacy negative card)
    # 2026-10-30: the earlier promote card is WITHDRAWN; the current card must be negative.
    run_card = None
    for p in DOCS.glob("downloads/*-audit.json"):
        c = json.loads(p.read_text())
        if c.get("verdict") == "withdrawn":
            run_card = c
            break
    assert run_card is not None, "Withdrawn candidate audit card not found"
    assert run_card["ok_to_download_and_submit"] is False
    assert run_card["withdrawn"]["superseded_by"] == "evidence/run_card_20261030.json"
    current = json.loads((ROOT / "evidence/run_card_20261030.json").read_text())
    assert current["verdict"] == "negative" and current["ok_to_download_and_submit"] is False
    assert current["submission"]["submitted"] is False
    assert run_card["n_dots"] == 22163
    assert run_card["validator_output"]["all_passed"] is True
    assert run_card["correlation_overlap_vs_registry"]["passes_lane"] is True
    assert len(run_card["submission_note_140"]) <= 140
    # Homepage and executive summary advertise the download
    assert "OK to download and submit" not in index
    assert "DO NOT SUBMIT" in index and "DO NOT SUBMIT" in exec_html
    assert run_card["raster_sha256"][:16] in exec_html
    assert "downloads/gemsdoesass2-sparse-blind-conduit-22163" in exec_html
    # Research artifacts remain marked research only
    artifacts = (DOCS / "hvfd-exp3.html").read_text()
    assert "Research only" in artifacts and "DO NOT SUBMIT" in artifacts
    assert "localhost" not in index and "127.0.0.1" not in index


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
