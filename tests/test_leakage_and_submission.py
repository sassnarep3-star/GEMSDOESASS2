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


def test_gate1_single_feature_leakage_canary() -> None:
    canary = json.loads((ROOT / "evidence" / "leakage_canary.json").read_text(encoding="utf-8"))
    assert canary["n_features_tested"] == 54
    assert canary["canary_passed"] is True
    assert canary["auc_limit"] == 0.90
    assert 0.50 <= canary["max_symmetric_auc"] <= 0.90
    assert canary["n_leaking_features"] == 0
    assert len(canary["features"]) == 54
    for feat in canary["features"]:
        assert feat["leaks_gt_0p90"] is False
        assert feat["symmetric_roc_auc"] <= 0.90


def test_gate2_holdout_monotonic_progression_and_strict_labels() -> None:
    hvfd = json.loads((ROOT / "evidence" / "hvfd_experiments.json").read_text(encoding="utf-8"))
    prim = hvfd["primary_holdout_buffered_loqo"]
    sec = hvfd["secondary_holdout_blind_quadrants_8km"]

    assert prim["evidence_class"] == "HOLDOUT-DTI"
    assert sec["evidence_class"] == "HOLDOUT-DTI"
    b = prim["scores"]
    for arm_val in b.values():
        assert arm_val["evidence_class"] == "HOLDOUT-DTI"
        assert arm_val["withheld_positive_pixels"] == 11_321

    d_slope = b["single_slope"]["dti"]
    d_rand = b["random_37654"]["dti"]
    d_fair = b["fair_h33"]["dti"]
    d_exp1 = b["EXP1_zero_cat_hydro_piedmont"]["dti"]
    d_exp2 = b["EXP2_hvfd_dual_population"]["dti"]
    d_exp3 = b["EXP3_hvfd_collinear_sharpened"]["dti"]

    assert d_slope < d_rand < d_fair < d_exp1 < d_exp2 < d_exp3
    paired = prim["paired_differences"]["fair_h33"]
    assert paired["delta"] > 0.020
    assert paired["ci95"][0] > 0.010

    blind = sec["scores"]
    assert blind["EXP3_blind_collinear"]["dti"] > blind["EXP1_blind_quadrant"]["dti"]
    assert blind["EXP3_blind_collinear"]["dti"] > 4.0 * blind["single_slope_blind"]["dti"]
    assert blind["EXP3_blind_collinear"]["dti"] > 9.5 * blind["random_37654"]["dti"]


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


def test_gate3_uniqueness_against_registry() -> None:
    uniq = json.loads((ROOT / "evidence" / "uniqueness_audit.json").read_text(encoding="utf-8"))
    assert uniq["n_unique_registry_rasters_checked"] >= 400
    assert uniq["all_uniqueness_gates_passed"] is True
    assert abs(uniq["worst_pre_placement_spearman"]["pre_placement_spearman"]) <= 0.90
    assert abs(uniq["worst_post_placement_spearman"]["post_placement_spearman"]) <= 0.90
    assert uniq["worst_discrete_3px_overlap"]["forward_3px_overlap"] <= 0.70

    # Verify EXP-2 duplicate stop was logged per Rule 1
    per_exp = uniq["per_experiment_gate_summary"]
    assert per_exp["EXP2_hvfd_dual_population"]["all_uniqueness_gates_passed"] is False
    assert per_exp["EXP2_hvfd_dual_population"]["max_discrete_3px_overlap"] > 0.70
    assert per_exp["EXP3_hvfd_collinear_sharpened"]["all_uniqueness_gates_passed"] is True


def test_gate4_promoted_geotiff_and_zip_portal_contract() -> None:
    rc = json.loads((ROOT / "evidence" / "hvfd_exp3_run_card.json").read_text(encoding="utf-8"))
    tif_path = ROOT / rc["raster_path"]
    zip_path = ROOT / "docs" / "downloads" / rc["zip_filename"]
    assert tif_path.exists(), f"Missing promoted GeoTIFF: {tif_path}"
    assert zip_path.exists(), f"Missing promoted ZIP: {zip_path}"

    # Cryptographic integrity
    assert _sha256(tif_path) == rc["raster_sha256"]
    assert _sha256(zip_path) == rc["zip_sha256"]

    # Direct rasterio inspection for DrivenData portal safety
    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert ds.dtypes[0] == "float32"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert ds.nodata is None
        arr = ds.read(1)

    assert arr.size == 12_279_160
    assert int(np.isnan(arr).sum()) == 0, "Zero NaNs permitted anywhere in zeros-mode portal GeoTIFF"
    assert int(np.isinf(arr).sum()) == 0, "Zero Infs permitted"
    assert float(arr.min()) >= 0.0
    assert float(arr.max()) <= 1.0

    # Shared template validator check against footprint & catalogue
    data_dir = ROOT / ".cache" / "gems_data"
    if (data_dir / "example_submission.tif").exists():
        grid_obj = load_grid(data_dir)
        val = v57.validate(tif_path, footprint=grid_obj.footprint, catalogue=grid_obj.catalogue)
        assert val["all_checks_passed"] is True
        assert val["n_nan"] == 0
        assert val["n_infinite"] == 0
        assert val["checks"]["outside_footprint_zero"] is True
        assert val["on_catalogue_positive_pixels"] == 0
        assert val["emitted_positive_pixels"] == 37_654

    # ZIP integrity
    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.testzip() is None
        names = zf.namelist()
        assert names == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == rc["raster_sha256"]


def test_gate5_run_card_and_nine_focus_sites_completeness() -> None:
    rc = json.loads((ROOT / "evidence" / "hvfd_exp3_run_card.json").read_text(encoding="utf-8"))
    for key in (
        "hypothesis",
        "mechanism",
        "named_non_fault_process_mimic",
        "holdout_dti",
        "correlation_and_overlap_vs_registry",
        "raster_sha256",
        "validator_output",
        "submission_name",
        "submission_note",
        "verdict",
    ):
        assert key in rc, f"Missing required Run Card key: {key}"

    assert rc["verdict"] == "promote"
    note = rc["submission_note"]
    assert 1 <= len(note) <= 140
    assert rc["submission_note_chars"] == len(note)

    nine = json.loads((ROOT / "evidence" / "nine_sites_audit.json").read_text(encoding="utf-8"))
    expected_sites = [
        "GEMSDOE24",
        "GEMSDOE25",
        "GEMSDOE27",
        "GEMSDOE28",
        "GEMSDOE30",
        "GEMSDOE31",
        "GEMSDOE32",
        "GEMSDOE33",
        "GEMSDOE36",
    ]
    assert [row["site"] for row in nine["sites"]] == expected_sites
    for row in nine["sites"]:
        hb = row["historic_best"]
        assert hb["overlap_3px_with_gemsdoesass2"] < 0.70
        assert "ORGANIZER-CONFIRMED" in hb["score_label"]
