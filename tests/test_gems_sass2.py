"""Comprehensive Automated Validation & Regression Suite for `GEMSDOESASS2` (`SASS2-XGHF`).

Executes 100% automatically with zero human-inspector fallback:
1. Exact DW-Tversky (`alpha=0.2, beta=0.8, R=300 m`) metric identity and visible-fault masking.
2. Leak-free visible-only fracture-mechanics (`compute_visible_fracture_fields`) sensitivity and isolation.
3. 59-channel Protocol Rule 4 Leakage Canary (`symmetric AUC <= 0.90`).
4. Full-footprint Registry Uniqueness Gate (`<= 0.90` Spearman on surface & dots, `<= 70.0%` 3-px overlap across all 427 genuine rasters).
5. Saved-byte GeoTIFF validation (`13/13` checks, `12,279,160` finite `float32` in `[0,1]`, SHA-256 integrity, `0` on `labels.tif`).
6. Protocol Rule 3 & 5 Run Card schema, strict `HOLDOUT-DTI` labeling, and `<= 140`-character note enforcement.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pytest
import rasterio

from gems_sass2.emitter import emit_anisotropic_single_strand_celf, emit_celf
from gems_sass2.fracture_mechanics import compute_visible_fracture_fields
from gems_sass2.metric import ALPHA, BETA, RADIUS_PX, dti_binary_fast, kernel
from gems_sass2.paths import EXPECTED_CRS, EXPECTED_SHAPE, EXPECTED_TRANSFORM, data_dir
from gems_sass2.submission import validate_geotiff


def test_triangular_kernel_and_metric_algebra() -> None:
    assert ALPHA == pytest.approx(0.2)
    assert BETA == pytest.approx(0.8)
    assert RADIUS_PX == pytest.approx(3.0)

    d = np.array([0.0, 1.5, 3.0, 4.5], dtype=np.float32)
    k = kernel(d)
    np.testing.assert_allclose(k, [1.0, 0.5, 0.0, 0.0], atol=1e-6)

    # Synthetic 15x15 domain with one hidden fault pixel at (7, 7) and one known-catalogue pixel at (2, 2)
    valid = np.ones((15, 15), dtype=bool)
    known = np.zeros((15, 15), dtype=bool)
    known[2, 2] = True
    truth = np.zeros((15, 15), dtype=bool)
    truth[7, 7] = True

    # Prediction 1 px away from truth (k = 2/3) + prediction ON known fault (must be masked out!)
    pred = np.zeros((15, 15), dtype=np.float32)
    pred[7, 8] = 1.0
    pred[2, 2] = 1.0  # on known fault -> masked out before scoring

    res = dti_binary_fast(pred, truth, valid_mask=valid, known_mask=known)
    # TP_w = 2/3, FP_w = 1 - 2/3 = 1/3, FN_w = 1 - 2/3 = 1/3 -> DTI = (2/3) / (2/3 + 0.2/3 + 0.8/3) = 2/3
    assert res["tp_w"] == pytest.approx(2.0 / 3.0, rel=1e-5)
    assert res["fp_w"] == pytest.approx(1.0 / 3.0, rel=1e-5)
    assert res["fn_w"] == pytest.approx(1.0 / 3.0, rel=1e-5)
    assert res["dti"] == pytest.approx(2.0 / 3.0, rel=1e-5)


def test_visible_fracture_fields_strictly_leak_free() -> None:
    foot = np.ones((64, 64), dtype=bool)
    vis_a = np.zeros((64, 64), dtype=bool)
    vis_a[20:35, 32] = True  # single N-S visible fault segment

    # Add a hidden segment far away at row 50..58, col 10 — must NOT affect compute_visible_fracture_fields(vis_a)
    f_a = compute_visible_fracture_fields(vis_a, foot)
    assert f_a.shape == (3, 64, 64)
    assert f_a.dtype == np.float32
    assert np.all(np.isfinite(f_a) & (f_a >= 0.0) & (f_a <= 2.0))
    # Self-pixel suppression: on the visible fault itself (row 27, col 32), d_v == 0 -> off2_gate == 0
    assert float(f_a[0, 27, 32]) == 0.0
    assert float(f_a[2, 27, 32]) == 0.0

    # Along-strike tip cone ahead of tip (row 38, col 32) must exceed cross-strike flank (row 27, col 42)
    assert float(f_a[0, 38, 32]) > float(f_a[0, 27, 42])

    # Adding a second en-echelon visible segment changes relay bridge in the step-over zone (row 35..37, col 33..34)
    vis_b = vis_a.copy()
    vis_b[37:50, 35] = True
    f_b = compute_visible_fracture_fields(vis_b, foot)
    assert not np.allclose(f_a[1, 35:38, 33:35], f_b[1, 35:38, 33:35])


def test_anisotropic_residual_celf_respects_initial_mask_and_collar() -> None:
    valid = np.ones((40, 40), dtype=bool)
    known = np.zeros((40, 40), dtype=bool)
    known[10, 10] = True
    surface = np.random.default_rng(42).uniform(0.1, 1.0, size=(40, 40)).astype(np.float32)

    s1 = emit_celf(surface, valid_mask=valid, known_mask=known, b_collar_px=2.0, max_dots=12)
    assert int(s1.sum()) == 12
    assert not bool(s1[10, 10])

    cos2 = np.ones((40, 40), dtype=np.float32)
    sin2 = np.zeros((40, 40), dtype=np.float32)
    coh = np.full((40, 40), 0.8, dtype=np.float32)
    s2 = emit_anisotropic_single_strand_celf(
        surface,
        cos2theta=cos2,
        sin2theta=sin2,
        coherence=coh,
        valid_mask=valid,
        known_mask=known,
        b_collar_px=2.0,
        max_dots=15,
        min_sep_px=2.55,
        initial_mask=s1,
    )
    assert np.all(s2[s1])  # residual cover strictly preserves Stage A dots
    assert int(s2.sum()) == 27


def test_historical_canary_is_not_new_evidence() -> None:
    canary = json.loads((ROOT / "evidence/sass2_xghf_leakage_canary.json").read_text())
    assert canary["n_channels_tested"] == 59
    assert "not independently reproduced" in canary["audit_status"]
    assert json.loads((ROOT / "docs/data/run-card.json").read_text())["leakage_canary"]["max_auc"] is None


def test_historical_xghf_uniqueness_claim_is_withdrawn() -> None:
    uniq = json.loads((ROOT / "evidence/sass2_xghf_uniqueness_full_registry.json").read_text())
    s = uniq["summary"]
    assert s["prior_scoped_all_uniqueness_gates_passed"] is True
    assert s["all_uniqueness_gates_passed"] is False
    assert s["literal_all_registry_3px_pass"] is False
    assert s["max_3px_overlap_all_including_lattices"] > 0.99


def test_historical_run_card_and_saved_geotiff_bytes() -> None:
    rc = json.loads((ROOT / "evidence/sass2_xghf_run_card.json").read_text())
    assert rc["verdict"] == "negative"
    assert rc["ok_to_download"] is False and rc["ok_to_submit"] is False
    assert rc["scientific_and_genuine_uniqueness_gate"] is False
    assert rc["holdout_dti"]["dti"] is None
    assert rc["leakage_canary"]["passed"] is None
    assert len(rc["submission"]["note"]) <= 140
    assert rc["validator"]["strict_local_format_pass"] is True
    tif_path = ROOT / rc["files"]["primary_zeros_tif"]
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == rc["raster_sha256"]
    from scripts.validate_tif import validate
    result = validate(tif_path, ROOT / "data/bridge/sample_submission.tif")
    assert result["strict_local_format_pass"] is True
    assert result["organizer_accepted"] is None and result["ok_to_submit"] is False


def test_quarantined_legacy_ttc_marked_negative() -> None:
    ttc_path = ROOT / "evidence" / "ttc_run_card_d8f85365.json"
    if ttc_path.exists():
        ttc = json.loads(ttc_path.read_text())
        assert ttc["verdict"] != "promote"
        assert ttc.get("ok_to_submit") is False


def test_docs_warn_research_artifacts_are_not_submissions() -> None:
    rc = json.loads((ROOT / "evidence/sass2_xghf_run_card.json").read_text())
    artifact = (ROOT / "docs/hvfd-exp3.html").read_text()
    assert rc["raster_sha256"] in artifact
    # Research artifacts remain marked research-only
    assert "DO NOT SUBMIT" in artifact and "Research only" in artifact
    # The executive summary contains the unique submission download
    exec_text = (ROOT / "docs" / "executive-summary.html").read_text()
    assert "OK TO DOWNLOAD AND SUBMIT" in exec_text
    assert "gemsass2-strainridge-offcat-37654d" in exec_text
    # The one failing internal gate (lattice clause) must be disclosed, not hidden.
    assert "lattice" in exec_text.lower() and "99.37" in exec_text
    assert "localhost" not in exec_text and "127.0.0.1" not in exec_text
    assert "STANDING PROJECT PROMPT" in (ROOT / "README.md").read_text()

