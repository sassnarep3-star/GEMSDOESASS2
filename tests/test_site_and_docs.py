"""Automated verification of GitHub Pages HTML/assets, local links, copyable metadata, and README."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def test_github_pages_files_and_local_links_exist() -> None:
    assert (DOCS / ".nojekyll").exists()
    assert (DOCS / "styles.css").stat().st_size > 1000
    html_pages = [
        DOCS / "index.html",
        DOCS / "executive-summary.html",
        DOCS / "forensics-and-methodology.html",
    ]
    for page in html_pages:
        assert page.exists(), f"Missing page: {page}"
        text = page.read_text(encoding="utf-8")
        for attr_val in re.findall(r'(?:href|src)="([^"]+)"', text):
            if attr_val.startswith(("http://", "https://", "#", "mailto:")):
                continue
            clean = attr_val.split("#")[0].split("?")[0]
            if not clean:
                continue
            target = (page.parent / clean).resolve()
            assert target.exists(), f"Broken relative asset/link '{attr_val}' in {page.name} -> {target}"
            if target.is_file():
                assert target.stat().st_size > 0, f"Empty asset '{attr_val}' in {page.name}"


def test_index_top_download_and_copy_metadata_match_run_card() -> None:
    rc = json.loads((ROOT / "evidence" / "run_card.json").read_text(encoding="utf-8"))
    idx = (DOCS / "index.html").read_text(encoding="utf-8")

    assert f'downloads/{rc["raster_filename"]}' in idx
    assert f'downloads/{rc["zip_filename"]}' in idx
    assert f'data-copy="{rc["submission_name"]}"' in idx
    assert f'data-copy="{rc["submission_note"]}"' in idx
    assert f'data-copy="{rc["raster_sha256"]}"' in idx
    assert len(rc["submission_note"]) <= 140


def test_nine_focus_sites_and_readme_links() -> None:
    exec_html = (DOCS / "executive-summary.html").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for site in (
        "GEMSDOE24",
        "GEMSDOE25",
        "GEMSDOE27",
        "GEMSDOE28",
        "GEMSDOE30",
        "GEMSDOE31",
        "GEMSDOE32",
        "GEMSDOE33",
        "GEMSDOE36",
    ):
        assert site in exec_html, f"Missing {site} in executive-summary.html"
        assert site in readme, f"Missing {site} in README.md"

    # Check all relative markdown links in README.md exist on disk
    for md_link in re.findall(r"\]\(([^)]+)\)", readme):
        if md_link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = md_link.split("#")[0].strip()
        if not clean:
            continue
        target = (ROOT / clean).resolve()
        assert target.exists(), f"Broken relative link in README.md: {md_link} -> {target}"
