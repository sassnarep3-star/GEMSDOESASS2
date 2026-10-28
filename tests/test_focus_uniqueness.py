"""Unit tests for scripts/focus_uniqueness_check.py gate helpers.

The helpers replace distance-transform and rankdata shortcuts for speed, so each
is checked against a slow reference implementation here.
"""
import importlib.util
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

SPEC = importlib.util.spec_from_file_location(
    "focus_uniqueness_check",
    Path(__file__).resolve().parents[1] / "scripts" / "focus_uniqueness_check.py",
)
fuc = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fuc)


def test_overlap_matches_bruteforce():
    rng = np.random.default_rng(1)
    cand = rng.integers(0, 200, size=(300, 2)).astype(float)
    other = rng.integers(0, 200, size=(150, 2)).astype(float)
    brute = np.mean([np.min(np.hypot(*(other - c).T)) <= 3.0 for c in cand])
    assert abs(fuc.overlap_3px(cand, other) - brute) < 1e-12


def test_overlap_empty_sets_are_zero():
    pts = np.array([[1.0, 1.0]])
    assert fuc.overlap_3px(np.empty((0, 2)), pts) == 0.0
    assert fuc.overlap_3px(pts, np.empty((0, 2))) == 0.0


def test_overlap_identical_sets_is_one():
    pts = np.array([[0.0, 0.0], [10.0, 10.0], [50.0, 3.0]])
    assert fuc.overlap_3px(pts, pts) == 1.0


def test_binary_fast_rank_matches_scipy():
    x = np.array([0, 1, 1, 0, 0, 1, 0, 0], dtype=np.float32)
    assert np.allclose(fuc._avg_ranks(x), rankdata(x))


def test_general_rank_matches_scipy_with_ties():
    x = np.array([0.2, 0.2, 0.7, 0.1, 0.7, 0.7, 0.0], dtype=np.float32)
    assert np.allclose(fuc._avg_ranks(x), rankdata(x))


def test_spearman_zero_variance_is_zero_and_symmetric():
    a = np.array([1, 0, 1, 0, 1], dtype=np.float32)
    const = np.zeros(5, dtype=np.float32)
    assert fuc.abs_spearman(a, const) == 0.0
    assert abs(fuc.abs_spearman(a, a) - 1.0) < 1e-12
    assert abs(fuc.abs_spearman(a, 1 - a) - 1.0) < 1e-12  # |rho| is sign-free


def test_probe_markers_detect_space_filling_rasters_only():
    assert fuc.is_probe("GEMSDOE24/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")
    assert fuc.is_probe("GEMSDOE/x/h58-continuous-pignistic.tif")
    assert not fuc.is_probe("GEMSDOE24/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif")
