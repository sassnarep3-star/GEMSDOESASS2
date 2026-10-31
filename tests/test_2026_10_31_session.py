"""Pin the 2026-10-31 H-CORRIDOR artifact to its own receipts.

Every number published on the site and in the README is asserted here against the
machine-readable evidence produced during the run, so the prose cannot silently
drift away from the measurement. Nothing here authorises a submission slot.

Key names below are quoted from the receipts themselves; if a receipt is
regenerated with a different schema, this file is expected to fail loudly rather
than silently pass.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "docs/downloads/gemsass2-hcorr-lineament-offcat-37654-20261031T000000Z"

# SHA-256 of the shipped artifact, measured on disk at build time.
ZEROS_TIF_SHA = "4367b360eda411afdba1a11db7dabd0a4744dbb3b679790b3d0fd77c2faf9c1f"
NAN_TIF_SHA = "bf89a685eb3b5ea3e582be54a29806eec48fa459ac9593362557802927214d43"

RUN_CARD = ROOT / "evidence/run_card_20261031.json"
FINAL = ROOT / ".cache/work/final_artifact.json"          # authoritative, gitignored
CORRIDOR = ROOT / "evidence/corridor_evaluation.json"
UNIQ = ROOT / "evidence/hcorr_uniqueness.json"
CAL = ROOT / "evidence/proxy_calibration.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text())


def _html(name: str) -> str:
    return (ROOT / "docs" / name).read_text()


# --------------------------------------------------------------------------
# 1. The bytes on disk are the bytes the receipts describe
# --------------------------------------------------------------------------
@pytest.mark.skipif(not (ROOT / "docs/downloads").exists(), reason="no downloads dir")
def test_shipped_zeros_tif_exists_and_is_hash_pinned():
    p = Path(f"{ART}-zeros.tif")
    assert p.exists(), "shipped artifact missing"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == ZEROS_TIF_SHA


@pytest.mark.skipif(not (ROOT / "docs/downloads").exists(), reason="no downloads dir")
def test_shipped_nan_twin_hash_pinned():
    p = Path(f"{ART}-nan.tif")
    assert p.exists(), "NaN twin missing"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == NAN_TIF_SHA


def test_run_card_shas_match_the_validator_receipt():
    """The run card's SHAs must equal what the validator actually hashed."""
    card = _load(RUN_CARD)
    assert card["validator"]["zeros"]["candidate_sha256"] == ZEROS_TIF_SHA
    assert card["validator"]["nan"]["candidate_sha256"] == NAN_TIF_SHA


@pytest.mark.skipif(not FINAL.exists(), reason="build cache not present (gitignored)")
def test_final_artifact_lists_both_shipped_files():
    final = _load(FINAL)
    tags = {f["tag"] for f in final["files"]}
    assert {"zeros", "nan"} <= tags
    for f in final["files"]:
        assert (ROOT / "docs/downloads" / f["tif"]).exists()
        assert (ROOT / "docs/downloads" / f["zip"]).exists()
        assert f["sha256"] == _load(RUN_CARD)["validator"][f["tag"]]["candidate_sha256"]
    assert final["mass"] == pytest.approx(37654.0)


def test_run_card_and_site_copy_are_identical():
    assert _load(RUN_CARD) == _load(ROOT / "docs/data/run-card-20261031.json")


# --------------------------------------------------------------------------
# 2. Every number the README publishes is a number a receipt contains
# --------------------------------------------------------------------------
def test_readme_publishes_the_pinned_sha_and_estimates():
    """After the merge of PR #40 this lane's file is a documented, NON-promoted
    candidate (IR-31-08): it must be present with its numbers, and it must be
    labelled as not the file to submit."""
    readme = (ROOT / "README.md").read_text()
    card = _load(RUN_CARD)
    assert card["validator"]["zeros"]["candidate_sha256"] in readme
    est = card["score_estimate"]
    for key in ("E1_within_family_contamination_regression",
                "E2_proxy_yield_ratio",
                "E3_peer_group_central_tendency"):
        assert f"{est[key]['value']:.4f}" in readme, f"README omits {key}"
    assert f"{est['quoted_central']:.2f}" in readme
    for v in est["quoted_range"]:
        assert f"{v:.2f}" in readme
    # and the demotion is explicit next to it
    assert "H-CORRIDOR" in readme
    assert "NOT PROMOTED" in readme


def test_readme_does_not_claim_an_organizer_confirmed_score():
    """The word may appear as a labelling *rule* (the standing prompt requires it);
    what must never appear is a number presented as an organizer-confirmed score."""
    readme = (ROOT / "README.md").read_text()
    assert re.search(r"ORGANIZER[- ]CONFIRMED[^\n]{0,40}?\d\.\d+", readme,
                     flags=re.IGNORECASE) is None
    # and no file in this repository may be described as having a confirmed score
    assert re.search(r"(?:organizer|drivendata)[^.\n]{0,60}confirm(?:ed|s)?[^.\n]{0,40}\d\.\d",
                     readme, flags=re.IGNORECASE) is None


def test_run_card_estimators_are_ordered_e1_ge_e2_ge_e3():
    """The quoted interval must actually span the three estimators."""
    est = _load(RUN_CARD)["score_estimate"]
    e1 = est["E1_within_family_contamination_regression"]["value"]
    e2 = est["E2_proxy_yield_ratio"]["value"]
    e3 = est["E3_peer_group_central_tendency"]["value"]
    lo, hi = est["quoted_range"]
    assert lo <= min(e1, e2, e3) and max(e1, e2, e3) <= hi
    assert min(e1, e2, e3) <= est["quoted_central"] <= max(e1, e2, e3)


# --------------------------------------------------------------------------
# 3. The gates, as recorded
# --------------------------------------------------------------------------
def test_format_gate_both_encodings_strict_pass():
    card = _load(RUN_CARD)["validator"]
    for enc in ("zeros", "nan"):
        assert card[enc]["strict_local_format_pass"] is True
        assert card[enc]["n_checks_passed"] >= 10
        assert card[enc]["organizer_accepted"] is None   # never inferred
        assert card[enc]["ok_to_submit"] is False        # format ≠ authority
    # ship the file the portal's [0,1] check cannot fire on
    assert card["zeros"]["portal_range_safe"] is True
    assert card["zeros"]["outside_bounds_encoding"] == "zeros_finite_outside"
    assert card["nan"]["outside_bounds_encoding"] == "masked_or_nan_outside"


def test_format_gate_grid_matches_the_sample():
    card = _load(RUN_CARD)["validator"]["zeros"]
    assert card["crs"] == "EPSG:32611"
    assert tuple(card["shape"]) == (3730, 3292)


def test_uniqueness_receipt_inside_limits():
    u = _load(UNIQ)
    assert u["n_references"] >= 50
    assert u["max_overlap_3px_pct"] <= u["limits"]["overlap_pct"]
    assert u["max_abs_spearman"] <= u["limits"]["abs_spearman"]
    assert u["passes_lane"] is True
    # and the run card quotes the same numbers
    card = _load(RUN_CARD)["uniqueness"]
    assert card["max_overlap_3px_pct"] == u["max_overlap_3px_pct"]
    assert card["max_abs_spearman"] == u["max_abs_spearman"]
    assert card["n_references"] == u["n_references"]


def test_leakage_canary_is_below_the_alarm():
    card = _load(RUN_CARD)["leakage_canary"]
    assert card["spatially_blocked_oof_auc"] < card["alarm_threshold"]


def test_in_sample_auc_is_reported_alongside_the_canary():
    """The gap between the two is the spatial generalisation gap; both must show."""
    model = _load(RUN_CARD)["model"]
    assert model["in_sample_auc"] > 0.85
    assert model["in_sample_auc"] > _load(RUN_CARD)["leakage_canary"]["spatially_blocked_oof_auc"]


# --------------------------------------------------------------------------
# 4. The negative science result is recorded, not smoothed over
# --------------------------------------------------------------------------
def test_candidate_loses_to_the_champion_on_the_proxy():
    """The artifact ships as a documented negative result. If a future run beats the
    champion, this test is expected to fail and must be updated together with the
    run card and the pages."""
    hold = _load(RUN_CARD)["holdout_dti"]
    assert hold["candidate"]["P_SGMC2"] < hold["champion_GEMSDOE32"]["P_SGMC2"]
    assert hold["candidate"]["P_SGMC0"] < hold["champion_GEMSDOE32"]["P_SGMC0"]
    # and it is the better file on the axis the hidden truth actually excludes
    assert hold["candidate"]["P_LABELS"] <= hold["champion_GEMSDOE32"]["P_LABELS"]
    assert "NEGATIVE" in hold["verdict"]


def test_sweep_deviation_is_disclosed():
    """IR-31-02: the shipped row is not the argmax and the reason is on record."""
    sw = _load(RUN_CARD)["sweep_deviation"]
    assert sw["argmax"] != sw["shipped"]
    assert "no-op" in sw["reason"].lower() or "NO-OP" in sw["reason"]
    assert 0 < sw["margin_pct"] < 5


@pytest.mark.skipif(not CORRIDOR.exists(), reason="corridor evaluation not present")
def test_champion_enrichment_is_a_real_signal():
    enr = _load(CORRIDOR)["enrichment"]
    assert enr["ratio_of_means"] > 1.5
    assert enr["mean_prob_champion"] > enr["mean_prob_random"]


@pytest.mark.skipif(not CAL.exists(), reason="proxy calibration not present")
def test_proxy_calibration_is_a_documented_null_result():
    """No proxy truth may be used to project a score while this holds."""
    cal = _load(CAL)
    assert cal["n_items"] >= 40
    # every proxy correlates weakly ...
    for key, c in cal["correlations"].items():
        assert abs(c["spearman"]) < 0.30, key
        assert c["p"] > 0.05, key
    # ... and every leave-one-out fit is worse than predicting the mean
    for key, f in cal["leave_one_out_linear_fits"].items():
        assert f["loo_r2"] < 0, key


@pytest.mark.skipif(not CAL.exists(), reason="proxy calibration not present")
def test_calibration_rows_are_deduplicated_by_pin():
    """Duplicate site keys across pin values silently corrupt any {key: row} dict."""
    cal = _load(CAL)
    sha_rows = [r for r in cal["rows"] if r["pin"] == "sha"]
    keys = [r["key"] for r in sha_rows]
    assert len(keys) == len(set(keys))
    assert len(keys) == 9


# --------------------------------------------------------------------------
# 5. The site cannot advertise a file it does not have
# --------------------------------------------------------------------------
@pytest.mark.parametrize("page", ["index.html", "executive-summary.html",
                                  "how-to-submit.html", "hypotheses.html",
                                  "method.html", "sources.html"])
def test_pages_exist_and_nav_targets_resolve(page):
    body = _html(page)
    for name in re.findall(r'href="([^"#:]+\.html)"', body):
        assert (ROOT / "docs" / name).exists(), f"{page} links missing {name}"


def test_executive_summary_advertises_exactly_one_download():
    """IR-S-41 / IR-31-08: only one file may advertise a download, and it is not ours."""
    body = _html("executive-summary.html")
    promoted = json.loads(
        (ROOT / "evidence/run_card_20261031.json").read_text())["promotion_status"]
    assert promoted["promoted"] is False
    assert promoted["advertised_as_download"] is False
    stems = set(re.findall(r'href="downloads/([^"]+)\.tif"', body))
    # the executive summary may name several artifacts, but exactly one is the promoted
    # submission, and our stem is not it
    ours = "gemsass2-hcorr-lineament-offcat-37654-20261031T000000Z"
    assert ours not in stems


def test_every_download_link_targets_an_existing_file():
    for page in ("index.html", "executive-summary.html", "how-to-submit.html"):
        for name in re.findall(r'href="downloads/([^"]+)"', _html(page)):
            assert (ROOT / "docs/downloads" / name).exists(), f"{page} → missing {name}"


def test_submission_note_fits_the_portal_limit():
    sub = _load(RUN_CARD)["submission"]
    assert sub["note_chars"] == len(sub["note"])
    assert sub["note_chars"] <= 140


def test_no_slot_was_spent():
    assert _load(RUN_CARD)["weekly_slots_spent"] == 0


def test_this_lane_does_not_claim_the_promotion():
    """IR-31-08: two 2026-10-31 lanes reached opposite promotion calls. The
    one-promoted-card invariant (IR-S-41) was resolved in favour of main's S3-RING
    file, so this lane's card must say so explicitly and must not set any
    download-approval flag."""
    card = _load(RUN_CARD)
    assert card["verdict"] == "promote-with-caveat"      # this lane's own honest verdict
    assert card["promotion_status"]["promoted"] is False
    assert card["promotion_status"]["advertised_as_download"] is False
    assert card["promotion_status"]["owner_may_reverse"] is True
    # no field anywhere in the card may assert download approval
    blob = json.dumps(card)
    assert '"ok_to_download_and_submit": true' not in blob
    assert '"ok_to_submit": true' not in blob
    # and no page may advertise our stem as a download
    for page in Path(ROOT / "docs").glob("*.html"):
        body = page.read_text()
        assert 'href="downloads/gemsass2-hcorr-lineament-offcat-37654' not in body, page.name
