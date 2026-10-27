from __future__ import annotations

import numpy as np

from gemsdoesass2.holdout import evaluate_surface, leakage_canary, make_segment_holdout, select_top_local_maxima


def four_quadrant_labels(shape: tuple[int, int] = (20, 20)) -> np.ndarray:
    labels = np.zeros(shape, dtype=bool)
    labels[2, 2] = True
    labels[2, -3] = True
    labels[-3, 2] = True
    labels[-3, -3] = True
    return labels


def test_whole_segments_are_withheld_exactly_once() -> None:
    footprint = np.ones((20, 20), dtype=bool)
    labels = four_quadrant_labels()
    holdout = make_segment_holdout(footprint, labels, buffer_px=1)
    assert len(holdout.folds) == 4
    assert holdout.n_segments == 4
    assert holdout.n_withheld_positive_pixels == int(labels.sum())
    all_hidden = np.zeros_like(labels)
    for fold in holdout.folds:
        assert not (all_hidden & fold.hidden).any()
        all_hidden |= fold.hidden
        # Every visible source excludes the buffered hidden neighborhood.
        assert not (fold.visible_catalogue & fold.hidden).any()
    assert np.array_equal(all_hidden, labels)


def test_nms_selector_is_deterministic_and_does_not_pad() -> None:
    surface = np.zeros((8, 8), dtype=np.float32)
    surface[1, 1] = 0.8
    surface[5, 5] = 0.9
    eligible = np.ones((8, 8), dtype=bool)
    output = select_top_local_maxima(surface, eligible, budget=2, nms_size=3)
    assert output.sum() == 2
    assert output[1, 1] and output[5, 5]


def test_holdout_evaluation_and_canary_report_required_fields() -> None:
    footprint = np.ones((20, 20), dtype=bool)
    labels = four_quadrant_labels()
    holdout = make_segment_holdout(footprint, labels, buffer_px=1)
    surface = np.zeros((20, 20), dtype=np.float32)
    surface[2, 2] = 1.0
    surface[2, -3] = 1.0
    surface[-3, 2] = 1.0
    surface[-3, -3] = 1.0
    # Give each fold at least one other local maximum after visible masking.
    surface[10, 10] = 0.5
    report = evaluate_surface(holdout, surface, pixel_size_m=100.0, budget=1, n_bootstraps=100)
    assert report["label"] == "HOLDOUT-DTI"
    assert report["n_withheld_positive_pixels"] == 4
    assert 0.0 <= report["pooled_dti"] <= 1.0
    assert report["ci95"]["low"] <= report["ci95"]["high"]
    canary = leakage_canary(holdout, {"surface": surface}, threshold=0.90)
    assert "max_auc" in canary["features"]["surface"]
