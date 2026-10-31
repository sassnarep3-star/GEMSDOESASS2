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
    """Exactly one candidate is advertised. Policy 2026-10-31: COLLAR4-HEX supersedes strain-ridge
    because it clears both literal uniqueness tests over 531 registry rasters and re-verifies 13/13
    on the saved bytes. The assertions track the *receipts on disk*, so a page cannot advertise a
    download that the gate JSON does not clear (IR-S-25); the r13 lattice disclosure must stay on both
    pages because that clause still fails for every interior placement (IR-S-21, IR-S-37)."""
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
    promoted = []
    for p in DOCS.glob("downloads/*-audit.json"):
        c = json.loads(p.read_text())
        if c.get("verdict") == "promote" and c.get("ok_to_download_and_submit"):
            promoted.append(c)
    assert len(promoted) == 1, f"exactly one promoted card may exist, found {len(promoted)}"
    run_card = promoted[0]
    assert run_card["n_dots"] == 37636
    assert run_card["dots_on_catalogue"] == 0
    assert run_card["validator_output"]["all_passed"] is True
    assert run_card["validator_output"]["values_in_0_1"] is True
    assert run_card["correlation_overlap_vs_registry"]["passes_lane"] is True
    assert run_card["correlation_overlap_vs_registry"]["max_overlap_3px_pct"] <= 70.0
    assert run_card["correlation_overlap_vs_registry"]["max_abs_spearman"] <= 0.90
    assert run_card["holdout_dti"]["evidence_class"] == "HOLDOUT-DTI"
    assert run_card["score_evidence"]["organizer_confirmed"] is False
    assert len(run_card["submission_note_140"]) <= 140
    # Its bytes must be the advertised bytes.
    promoted_tif = DOCS / "downloads" / run_card["artifact"]
    assert hashlib.sha256(promoted_tif.read_bytes()).hexdigest() == run_card["raster_sha256"]
    # The superseded headline keeps its history but must not be promotable.
    sup = json.loads((DOCS / "downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-audit.json").read_text())
    assert sup["verdict"].startswith("superseded") and sup["ok_to_download_and_submit"] is False
    assert sup["supersession_reason"]

    index = (DOCS / "index.html").read_text()
    exec_html = (DOCS / "executive-summary.html").read_text()
    for page in (index, exec_html):
        assert "ok to download and submit" in page.lower()
        assert "lattice" in page.lower(), "the failing lattice clause must be disclosed"
        assert "localhost" not in page and "127.0.0.1" not in page
    # Merged from origin/main (PR #33/#34): the sibling artifacts, the un-verifiable score class and the
    # superseded bytes stay on the page, and the historical raster remains measurable but not promotable.
    assert "0.2778" in exec_html and "USER-REPORTED / UNVERIFIED" in exec_html
    assert "NOT ESTIMABLE" in exec_html
    assert "not an organizer score" in exec_html.lower()
    assert "downloads/gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif" not in index
    historical = DOCS / "downloads" / "gemsass2-strainridge-offcat-37654d-20261030T025503Z-zeros.tif"
    assert historical.exists()
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == "6d00f58a35005a253e352e21c8adde0e108aa0abb4b810db9797af89d94dd615"
    for page in (index, exec_html):
        assert "do not submit" in page.lower()
        assert "not estimable" in page.lower()
        assert "lattice" in page.lower()
    assert "99.37" in exec_html
    assert "MODEL ESTIMATE" in exec_html
    assert "not an organizer score" in exec_html.lower() or "NOT organizer-confirmed" in exec_html
    assert "gemsass2-strainridge-offcat-37654d-20261030T025503Z" in exec_html
    assert "downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif" in index
    assert "Supersedes" in exec_html and "IR-S-34" in exec_html
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
