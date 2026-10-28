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


def test_index_top_download_and_copy_metadata_match_run_card() -> None:
    # Landing page = SASS2-XGHF (the only file passing every genuine gate).
    rc = json.loads((ROOT / "evidence" / "sass2_xghf_run_card.json").read_text(encoding="utf-8"))
    txt = (DOCS / "index.html").read_text(encoding="utf-8")
    sub = rc["submission"]
    assert f'data-copy="{sub["name"]}"' in txt
    assert f'data-copy="{sub["note"]}"' in txt
    assert f'data-copy="{rc["raster_sha256"]}"' in txt
    assert len(sub["note"]) <= 140
    assert "downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif" in txt
    # The HVFD page keeps its audit copy buttons, but must be labelled do-not-submit.
    hv = json.loads((ROOT / "evidence" / "hvfd_exp3_run_card.json").read_text(encoding="utf-8"))
    hv_txt = (DOCS / "hvfd-exp3.html").read_text(encoding="utf-8")
    assert f'data-copy="{hv["submission_name"]}"' in hv_txt
    assert "DO NOT SUBMIT THIS FILE" in hv_txt


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

    for md_link in re.findall(r"\]\(([^)]+)\)", readme):
        if md_link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean = md_link.split("#")[0].strip()
        if not clean:
            continue
        target = (ROOT / clean).resolve()
        assert target.exists(), f"Broken relative link in README.md: {md_link} -> {target}"
