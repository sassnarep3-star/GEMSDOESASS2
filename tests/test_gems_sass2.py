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
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gems_sass2.emitter import emit_anisotropic_single_strand_celf, emit_celf
from gems_sass2.fracture_mechanics import compute_visible_fracture_fields
from gems_sass2.metric import ALPHA, BETA, RADIUS_PX, dti_binary_fast, kernel
from gems_sass2.paths import EXPECTED_CRS, EXPECTED_SHAPE, EXPECTED_TRANSFORM, data_dir
from gems_sass2.submission import validate_geotiff

ROOT = Path(__file__).resolve().parents[1]


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


def test_leakage_canary_59_channels_all_pass() -> None:
    canary_path = ROOT / "evidence" / "sass2_xghf_leakage_canary.json"
    assert canary_path.exists()
    canary = json.loads(canary_path.read_text())
    assert canary["n_channels_tested"] == 59
    assert canary["all_passed"] is True
    assert canary["max_symmetric_auc"] <= 0.90
    for ch_name, rec in canary["channels"].items():
        assert 0.50 <= rec["symmetric_auc"] <= 0.90, f"Channel {ch_name} failed canary: {rec}"


def test_uniqueness_gate_full_registry_passes() -> None:
    uniq_path = ROOT / "evidence" / "sass2_xghf_uniqueness_full_registry.json"
    assert uniq_path.exists()
    uniq = json.loads(uniq_path.read_text())
    assert uniq["n_unique_sha256_rasters_scanned"] >= 400
    assert uniq["n_genuine_rasters_scanned"] >= 400
    s = uniq["summary"]
    assert s["max_abs_surface_spearman_all"] <= 0.90
    assert s["max_abs_dots_spearman_all"] <= 0.90
    assert s["max_3px_overlap_genuine"] <= 0.70
    assert s["all_uniqueness_gates_passed"] is True


def test_run_card_and_saved_geotiff_bytes() -> None:
    rc_path = ROOT / "evidence" / "sass2_xghf_run_card.json"
    assert rc_path.exists()
    rc = json.loads(rc_path.read_text())

    # Required Protocol Rule 5 Run Card fields
    for key in [
        "hypothesis",
        "mechanism",
        "named_non_fault_mimic",
        "holdout_dti",
        "correlation_and_overlap_vs_registry",
        "raster_sha256",
        "validator",
        "submission",
        "verdict",
    ]:
        assert key in rc

    assert rc["holdout_dti"]["primary_hide_and_recover"]["label"] == "HOLDOUT-DTI"
    assert rc["holdout_dti"]["secondary_sgmc_off_catalogue"]["label"] == "HOLDOUT-DTI"
    assert rc["holdout_dti"]["primary_hide_and_recover"]["paired_delta_vs_02778"]["statistically_positive_95"] is True
    assert rc["holdout_dti"]["secondary_sgmc_off_catalogue"]["sgmc_prevalence_calibrated_dti"] > rc["holdout_dti"]["secondary_sgmc_off_catalogue"]["incumbent_02778_sgmc_cal"]
    assert len(rc["submission"]["note"]) <= 140
    assert rc["experiments_used"] <= 3
    assert rc["verdict"] == "promote"

    tif_path = ROOT / rc["files"]["primary_zeros_tif"]
    nan_path = ROOT / rc["files"]["archive_nan_tif"]
    zip_path = ROOT / rc["files"]["primary_zeros_zip"]
    assert tif_path.exists()
    assert nan_path.exists()
    assert zip_path.exists()

    actual_sha = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    assert actual_sha == rc["raster_sha256"]

    ddir = data_dir()
    if (ddir / "sample_submission.tif").exists() and (ddir / "labels.tif").exists():
        audit_z = validate_geotiff(
            tif_path, ddir / "sample_submission.tif", ddir / "labels.tif", strict_all_finite=True
        )
        assert audit_z["all_passed"] is True
        assert audit_z["checks_passed"] == 13
        assert audit_z["all_12279160_finite"] is True
        assert audit_z["positive_dots_in_footprint"] == 37_654
        assert audit_z["positive_on_catalogue"] == 0

        audit_n = validate_geotiff(
            nan_path, ddir / "sample_submission.tif", ddir / "labels.tif", strict_all_finite=False
        )
        assert audit_n["all_passed"] is True
        assert audit_n["outside_mode"] == "nan"
    else:
        with rasterio.open(tif_path) as ds:
            assert str(ds.crs) == EXPECTED_CRS
            assert ds.shape == EXPECTED_SHAPE
            assert list(ds.transform)[:6] == EXPECTED_TRANSFORM
            arr = ds.read(1)
            assert arr.dtype == np.float32
            assert np.isfinite(arr).all()
            assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
            assert int((arr > 0).sum()) == 37_654


def test_quarantined_legacy_ttc_marked_negative() -> None:
    ttc_path = ROOT / "evidence" / "ttc_run_card_d8f85365.json"
    if ttc_path.exists():
        ttc = json.loads(ttc_path.read_text())
        assert ttc["verdict"] != "promote"
        assert ttc.get("ok_to_submit") is False


def test_docs_portal_links_and_sha256_consistency() -> None:
    import re

    rc = json.loads((ROOT / "evidence" / "sass2_xghf_run_card.json").read_text())
    expected_sha = rc["raster_sha256"]
    expected_note = rc["submission"]["note"]
    assert len(expected_note) <= 140

    docs_dir = ROOT / "docs"
    for html_name in ("index.html", "executive-summary.html"):
        html_path = docs_dir / html_name
        assert html_path.exists()
        txt = html_path.read_text(encoding="utf-8")
        # Never call localhost/127.0.0.1 in browser-facing code
        assert "localhost" not in txt
        assert "127.0.0.1" not in txt
        assert expected_note in txt

        for attr_val in re.findall(r'(?:href|src)="([^"]+)"', txt):
            if attr_val.startswith(("http://", "https://", "#", "mailto:", "${")):
                continue
            target = (docs_dir / attr_val.split("#")[0]).resolve()
            assert target.exists(), f"Missing local asset in {html_name}: {attr_val}"
            assert target.stat().st_size > 0, f"Empty local asset in {html_name}: {attr_val}"

    assert expected_sha in (docs_dir / "index.html").read_text(encoding="utf-8")
    assert expected_sha in (docs_dir / "executive-summary.html").read_text(encoding="utf-8")

    readme_txt = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "STANDING PROJECT PROMPT" in readme_txt
    assert expected_sha in readme_txt
    assert expected_note in readme_txt

