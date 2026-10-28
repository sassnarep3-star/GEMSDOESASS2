"""Automated end-to-end verification of GEMSDOESASS2 gates, GeoTIFF contract, and Run Card."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

from gems57 import validate as v57
from gems57.grid import load_grid
from gems_sass2.audit import disk_struct
from gems_sass2.features import ALL_FEATURE_NAMES, MECH_FEATURE_NAMES, STATIC_FEATURE_NAMES

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_feature_stack_excludes_catalogue_distance_leakage() -> None:
    assert len(STATIC_FEATURE_NAMES) == 48
    assert len(MECH_FEATURE_NAMES) == 6
    assert len(ALL_FEATURE_NAMES) == 54
    assert "dist_known_fault_px" not in ALL_FEATURE_NAMES
    for name in ALL_FEATURE_NAMES:
        assert "dist_known_fault" not in name.lower()


def test_prior_canary_is_archival_not_a_new_pass() -> None:
    canary = json.loads((ROOT / "evidence/leakage_canary.json").read_text())
    assert canary["n_features_tested"] == 54
    assert "not independently reproduced" in canary["audit_status"]
    assert json.loads((ROOT / "docs/data/run-card.json").read_text())["leakage_canary"]["max_auc"] is None


def test_prior_holdout_is_not_treated_as_a_current_score() -> None:
    historical = json.loads((ROOT / "evidence/hvfd_experiments.json").read_text())
    assert "not independently reproduced" in historical["audit_status"]
    card = json.loads((ROOT / "evidence/hvfd_exp3_run_card.json").read_text())
    assert card["holdout_dti"]["dti"] is None
    assert card["holdout_dti"]["ci95"] is None
    assert card["verdict"] == "negative"


def test_disk3_fast_offset_equivalence_with_binary_dilation() -> None:
    rng = np.random.default_rng(42)
    a = rng.random((120, 140)) < 0.02
    b = rng.random((120, 140)) < 0.03
    st3 = disk_struct(3.0)
    assert int(st3.sum()) == 29
    dil_b = ndi.binary_dilation(b, structure=st3)
    expected_hits = int((a & dil_b).sum())

    H, W = a.shape
    cy, cx = np.nonzero(a)
    st3_oy, st3_ox = np.nonzero(st3)
    st3_oy = st3_oy - 3
    st3_ox = st3_ox - 3
    b_pad = np.zeros((H + 6, W + 6), dtype=bool)
    b_pad[3 : H + 3, 3 : W + 3] = b
    any_hit = np.zeros(len(cy), dtype=bool)
    for oy, ox in zip(st3_oy, st3_ox):
        any_hit |= b_pad[cy + 3 + oy, cx + 3 + ox]
    assert int(any_hit.sum()) == expected_hits


def test_literal_registry_stop_is_not_exempted() -> None:
    uniq = json.loads((ROOT / "evidence/uniqueness_audit.json").read_text())
    assert uniq["prior_scoped_all_uniqueness_gates_passed"] is True
    assert uniq["all_uniqueness_gates_passed"] is False
    witness = uniq["literal_lattice_check"]
    assert (witness["candidate_dots"], witness["within_3px"]) == (37654, 37617)
    assert witness["fraction"] > .70
    assert uniq["per_experiment_gate_summary"]["EXP3_hvfd_collinear_sharpened"]["all_uniqueness_gates_passed"] is False
    assert uniq["per_experiment_gate_summary"]["EXP2_hvfd_dual_population"]["all_uniqueness_gates_passed"] is False


def test_historical_tiff_and_zip_integrity_is_not_approval() -> None:
    from scripts.validate_tif import validate
    rc = json.loads((ROOT / "evidence/hvfd_exp3_run_card.json").read_text())
    tif_path = ROOT / rc["raster_path"]
    zip_path = ROOT / "docs/downloads" / rc["zip_filename"]
    assert _sha256(tif_path) == rc["raster_sha256"]
    assert _sha256(zip_path) == rc["zip_sha256"]
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.testzip() is None and zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == rc["raster_sha256"]
    result = validate(tif_path, ROOT / "data/bridge/sample_submission.tif")
    assert result["strict_local_format_pass"] is True
    assert result["organizer_accepted"] is None and result["ok_to_submit"] is False


def test_negative_run_card_and_nine_focus_sites() -> None:
    rc = json.loads((ROOT / "docs/data/run-card.json").read_text())
    for key in ("hypothesis", "mechanism", "named_non_fault_process", "holdout_dti",
                "correlation_overlap_vs_registry", "raster_sha256", "validator_output",
                "submission_name", "note", "verdict"):
        assert key in rc
    assert rc["verdict"] == "negative" and rc["ok_to_submit"] is False
    assert rc["raster_sha256"] is None and rc["submission_name"] is None
    assert rc["holdout_dti"]["dti"] is None and len(rc["note"]) <= 140
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    expected = {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    assert {r["site"] for r in audit["historical_sites"]} == expected
    for row in audit["historical_sites"]:
        assert not row["unique_against_nine_under_dot_rule"]
        assert row["historical_score_evidence"].startswith("USER-REPORTED")
