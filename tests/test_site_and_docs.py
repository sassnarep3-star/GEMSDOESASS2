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


def test_current_decision_is_fail_closed_and_historical_tif_is_not_advertised() -> None:
    """The literal lattice rule and shared-evaluator failures block every candidate."""
    import hashlib

    rc = json.loads((ROOT / "evidence/unique_run_card_cc522684.json").read_text())
    assert rc["verdict"] == "negative"
    assert rc["ok_to_submit"] is False and rc["ok_to_download_and_submit"] is False
    recheck = json.loads((ROOT / "evidence/lattice_gate_recheck_20261030.json").read_text())
    candidate = recheck["candidates"][0]
    assert candidate["literal_lattice_gate_pass"] is False
    tif = DOCS / "downloads" / candidate["file"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == candidate["sha256"]

    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "do not submit" in page.lower()
        assert "not estimable" in page.lower()
        assert "lattice" in page.lower()
        assert "localhost" not in page and "127.0.0.1" not in page
    assert "0.2778" in exec_html and "USER-REPORTED / UNVERIFIED" in exec_html
    assert "NOT ESTIMABLE" in exec_html
    assert "OK TO DOWNLOAD AND SUBMIT" not in exec_html
    assert "downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif" not in index
    # Archived strain-ridge bytes remain measurable but are not submission-authorized.
    historical = DOCS / "downloads" / "gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif"
    assert historical.exists()
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == "6d00f58a35005a253e352e21c8adde0e108aa0abb4b810db9797af89d94dd615"
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
