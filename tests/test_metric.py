"""Verify the vendored shared metric against the official DrivenData definition."""
from __future__ import annotations

import numpy as np
import pytest

from gems57 import metric


def test_hand_example_dot_at_100m() -> None:
    truth = np.zeros((11, 11), bool)
    truth[5, 5] = True
    pred = np.zeros((11, 11))
    pred[5, 6] = 1.0
    r = metric.dti_exact(pred, truth)
    assert r["tp"] == pytest.approx(2 / 3)
    assert r["fp"] == pytest.approx(1 / 3)
    assert r["fn"] == pytest.approx(1 / 3)
    assert r["dti"] == pytest.approx(2 / 3)


def test_dot_on_truth_and_at_300m() -> None:
    truth = np.zeros((11, 11), bool)
    truth[5, 5] = True
    on = np.zeros((11, 11))
    on[5, 5] = 1.0
    assert metric.dti_exact(on, truth)["dti"] == pytest.approx(1.0)
    far = np.zeros((11, 11))
    far[5, 8] = 1.0  # d = 3 px -> k = 0
    assert metric.dti_exact(far, truth)["dti"] == pytest.approx(0.0)


def test_exact_matches_bruteforce_random() -> None:
    rng = np.random.default_rng(76)
    for _ in range(25):
        truth = rng.random((14, 13)) < 0.08
        pred = np.where(rng.random((14, 13)) < 0.15, rng.random((14, 13)), 0.0)
        if not truth.any():
            continue
        a = metric.dti_exact(pred, truth)
        b = metric.dti_bruteforce(pred, truth)
        assert a["tp"] == pytest.approx(b["tp"], abs=1e-9)
        assert a["fp"] == pytest.approx(b["fp"], abs=1e-9)
        assert a["fn"] == pytest.approx(b["fn"], abs=1e-9)
        assert a["dti"] == pytest.approx(b["dti"], abs=1e-9)


def test_binary_matches_exact() -> None:
    rng = np.random.default_rng(7)
    truth = rng.random((20, 19)) < 0.06
    dots = rng.random((20, 19)) < 0.05
    a = metric.dti_binary(dots, truth)
    b = metric.dti_exact(dots.astype(float), truth)
    assert a["dti"] == pytest.approx(b["dti"], abs=1e-9)


def test_marginal_bar_algebra() -> None:
    assert metric.dti_from_components(3.0, 1.89, 2.0) == pytest.approx(0.6028, abs=1e-3)
    assert metric.marginal_inclusion_threshold(0.2778) == pytest.approx(0.05556)
