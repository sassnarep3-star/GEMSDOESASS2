from __future__ import annotations

import numpy as np

from gemsdoesass2.registry import rank_correlation


def test_binary_rank_correlation_is_exact_for_identical_masks() -> None:
    footprint = np.ones((10, 10), dtype=bool)
    left = np.zeros((10, 10), dtype=np.float32)
    left[2, 3] = 1.0
    left[7, 8] = 1.0
    correlation, mode, count = rank_correlation(left, left.copy(), footprint)
    assert correlation == 1.0
    assert mode == "exact_binary"
    assert count == 100


def test_constant_binary_surface_returns_safe_zero_correlation() -> None:
    footprint = np.ones((4, 4), dtype=bool)
    left = np.zeros((4, 4), dtype=np.float32)
    right = np.zeros((4, 4), dtype=np.float32)
    correlation, mode, _ = rank_correlation(left, right, footprint)
    assert correlation == 0.0
    assert mode == "exact_binary"


def test_continuous_rank_correlation_detects_reverse_order() -> None:
    footprint = np.ones((4, 4), dtype=bool)
    left = np.arange(16, dtype=np.float32).reshape(4, 4)
    right = left.max() - left
    correlation, mode, _ = rank_correlation(left, right, footprint)
    assert correlation == 1.0  # absolute correlation is used by the lane rule
    assert mode == "exact_spearman"
