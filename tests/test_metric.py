from __future__ import annotations

import numpy as np
import pytest

from gemsdoesass2.metric import dti_components, pooled_dti, worked_example


def test_dti_exact_hit_is_one() -> None:
    prediction = np.zeros((11, 11), dtype=np.float32)
    truth = np.zeros((11, 11), dtype=bool)
    prediction[5, 5] = 1.0
    truth[5, 5] = True
    result = dti_components(prediction, truth, pixel_size_m=100.0)
    assert result.dti == pytest.approx(1.0)
    assert result.true_positive_weight == pytest.approx(1.0)
    assert result.false_positive_weight == pytest.approx(0.0)
    assert result.false_negative_weight == pytest.approx(0.0)


def test_dti_triangular_credit_one_pixel_away() -> None:
    prediction = np.zeros((11, 11), dtype=np.float32)
    truth = np.zeros((11, 11), dtype=bool)
    prediction[5, 6] = 1.0
    truth[5, 5] = True
    result = dti_components(prediction, truth, pixel_size_m=100.0)
    # Kernel credit at 100 m with a 300 m radius is 2/3; the residual
    # prediction receives 1/3 false-positive weight.
    assert result.true_positive_weight == pytest.approx(2.0 / 3.0)
    assert result.false_negative_weight == pytest.approx(1.0 / 3.0)
    assert result.false_positive_weight == pytest.approx(1.0 / 3.0)
    assert result.dti == pytest.approx(2.0 / 3.0)


def test_nan_truth_is_not_silently_coerced_to_a_positive() -> None:
    prediction = np.zeros((5, 5), dtype=np.float32)
    truth = np.zeros((5, 5), dtype=np.float32)
    truth[2, 2] = np.nan
    result = dti_components(prediction, truth)
    assert result.n_truth_pixels == 0


def test_catalogue_mask_removes_visible_prediction_from_evaluation() -> None:
    prediction = np.zeros((11, 11), dtype=np.float32)
    truth = np.zeros((11, 11), dtype=bool)
    visible = np.zeros((11, 11), dtype=bool)
    prediction[2, 2] = 1.0
    visible[2, 2] = True
    truth[8, 8] = True
    result = dti_components(prediction, truth, catalogue_mask=visible)
    assert result.false_positive_weight == pytest.approx(0.0)
    assert result.dti == pytest.approx(0.0)


def test_pooled_dti_is_not_mean_of_fold_ratios() -> None:
    rows = np.asarray([[1.0, 0.0, 0.0], [0.0, 0.0, 9.0]])
    pooled = pooled_dti(rows)
    assert pooled == pytest.approx(1.0 / (1.0 + 0.8 * 9.0))
    assert pooled != pytest.approx(0.5)


def test_worked_example_rounds_to_expected_value() -> None:
    assert worked_example()["rounded_two_decimals"] == 0.6
