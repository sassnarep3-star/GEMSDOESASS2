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
    """Exactly one artifact is advertised as submittable, its bytes match its card, the
    gate that fails is disclosed, and no page claims an organizer receipt.

    Rewritten 2026-10-31: the previously promoted strain-ridge file is demoted to
    research-only because the catalogue claim behind it is not reproducible
    (IR-31-03) and it fails the literal lattice clause at 99.37%. Its receipts
    remain on file and are still asserted here so the demotion is auditable.
    """
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

    # The current promoted artifact: the H-CORRIDOR file, and only it.
    card = json.loads((ROOT / "evidence/run_card_20261031.json").read_text())
    assert card["verdict"] == "promote-with-caveat"
    assert card["weekly_slots_spent"] == 0
    stem = card["submission"]["stem"]
    promoted_tif = DOCS / "downloads" / f"{stem}-zeros.tif"
    assert hashlib.sha256(promoted_tif.read_bytes()).hexdigest() == (
        card["validator"]["zeros"]["candidate_sha256"])
    assert card["uniqueness"]["passes_lane"] is True
    assert card["uniqueness"]["max_overlap_3px_pct"] <= 70.0
    assert len(card["submission"]["note"]) <= 140
    # The science gate is negative and the card says so.
    hd = card["holdout_dti"]
    assert hd["candidate"]["P_SGMC2"] < hd["champion_GEMSDOE32"]["P_SGMC2"]
    assert "NEGATIVE" in hd["verdict"]

    # Exactly one download may be advertised as submittable.
    promoted = [c for c in
                (json.loads(p.read_text()) for p in (DOCS / "downloads").glob("*-audit.json"))
                if c.get("verdict") == "promote" and c.get("ok_to_download_and_submit")]
    assert len(promoted) <= 1

    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "ok to download and submit" in page.lower()
        assert "lattice" in page.lower(), "the lattice clause must be disclosed"
        assert "localhost" not in page and "127.0.0.1" not in page
    assert "99.37" in exec_html           # the strain-ridge file the clause blocks
    assert "53.92" in exec_html           # and this file's own margin
    assert "MODEL ESTIMATE" in exec_html
    assert "not an organizer score" in exec_html.lower() or "NOT organizer-confirmed" in exec_html
    assert stem in exec_html
    assert f"downloads/{stem}-zeros.tif" in index
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
