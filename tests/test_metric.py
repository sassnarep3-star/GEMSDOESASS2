import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gems.metric import dti_binary, dti_probabilistic, tri_kernel


def test_kernel():
    assert tri_kernel(np.array([0.0]))[0] == 1.0
    assert tri_kernel(np.array([3.0]))[0] == 0.0
    assert abs(tri_kernel(np.array([1.0]))[0] - 2 / 3) < 1e-12


def test_perfect_hit():
    t = np.zeros((20, 20), bool); t[10, 10] = True
    p = t.copy()
    assert dti_binary(p, t)["dti"] == 1.0


def test_one_px_offset():
    t = np.zeros((20, 20), bool); t[10, 10] = True
    p = np.zeros((20, 20), bool); p[10, 11] = True
    r = dti_binary(p, t)
    exp_T = 2 / 3
    exp = exp_T / (exp_T + 0.2 * (1 - exp_T) + 0.8 * (1 - exp_T))
    assert abs(r["dti"] - exp) < 1e-12


def test_fp_cheap_fn_costly():
    """alpha=0.2 vs beta=0.8: an extra FP dot hurts 4x less than a miss."""
    t = np.zeros((40, 40), bool); t[10, 10] = True; t[30, 30] = True
    hit_both = np.zeros((40, 40), bool); hit_both[10, 10] = True; hit_both[30, 30] = True
    hit_one_plus_fp = np.zeros((40, 40), bool); hit_one_plus_fp[10, 10] = True; hit_one_plus_fp[20, 0] = True
    assert dti_binary(hit_both, t)["dti"] > dti_binary(hit_one_plus_fp, t)["dti"]


def test_masking_removes_pixels():
    t = np.zeros((20, 20), bool); t[10, 10] = True; t[5, 5] = True
    p = np.zeros((20, 20), bool); p[10, 10] = True; p[5, 5] = True
    mask = np.ones((20, 20), bool); mask[5, 5] = False  # 5,5 masked out
    r = dti_binary(p, t, mask)
    assert r["n_truth"] == 1 and r["n_pred"] == 1 and r["dti"] == 1.0


if __name__ == "__main__":
    for f in [test_kernel, test_perfect_hit, test_one_px_offset,
              test_fp_cheap_fn_costly, test_masking_removes_pixels]:
        f()
        print(f.__name__, "PASS")


def test_probabilistic_equals_binary_on_binary_masks():
    """Official continuous form reduces exactly to the binary dot form for p in {0, 1}."""
    for seed in range(5):
        rng = np.random.default_rng(seed)
        t = rng.random((60, 60)) < 0.03
        p = rng.random((60, 60)) < 0.05
        b = dti_binary(p, t)["dti"]
        q = dti_probabilistic(p.astype(float), t)["dti"]
        assert abs(b - q) < 1e-9, (seed, b, q)


def test_half_probability_at_truth():
    """One truth pixel, p = 0.5 on it: TP = 0.5, FP = 0, FN = 0.5."""
    t = np.zeros((20, 20), bool); t[10, 10] = True
    p = np.zeros((20, 20)); p[10, 10] = 0.5
    r = dti_probabilistic(p, t)
    assert abs(r["TP"] - 0.5) < 1e-12 and abs(r["FP"]) < 1e-12 and abs(r["FN"] - 0.5) < 1e-12
    assert abs(r["dti"] - 0.5 / (0.5 + 0.8 * 0.5)) < 1e-12


def test_weighted_tp_is_max_not_sum():
    """Two dots both 1 px from one truth pixel: TP_w counts the best one (2/3), not 4/3."""
    t = np.zeros((20, 20), bool); t[10, 10] = True
    p = np.zeros((20, 20)); p[10, 11] = 1.0; p[11, 10] = 1.0
    r = dti_probabilistic(p, t)
    assert abs(r["TP"] - 2 / 3) < 1e-12
    assert abs(r["FP"] - 2 * (1 / 3)) < 1e-12  # each dot: 1 - k(1) = 1/3


def test_mixed_near_and_far_predictions_worked_example():
    t = np.zeros((40, 40), bool); t[10, 10] = True
    p = np.zeros((40, 40)); p[10, 11] = 1.0; p[10, 30] = 0.5
    r = dti_probabilistic(p, t)
    tp, fp, fn = 2 / 3, 1 / 3 + 0.5, 1 / 3
    assert abs(r["TP"] - tp) < 1e-12 and abs(r["FP"] - fp) < 1e-12 and abs(r["FN"] - fn) < 1e-12
    assert abs(r["dti"] - tp / (tp + 0.2 * fp + 0.8 * fn)) < 1e-12


def test_empty_truth_and_empty_prediction():
    t = np.zeros((10, 10), bool)
    p = np.zeros((10, 10)); p[5, 5] = 0.7
    assert dti_probabilistic(p, t)["dti"] == 0.0
    t[2, 2] = True
    assert dti_probabilistic(np.zeros((10, 10)), t)["dti"] == 0.0


def test_range_and_nan_guards():
    t = np.zeros((10, 10), bool); t[5, 5] = True
    with pytest.raises(ValueError):
        dti_probabilistic(np.full((10, 10), 1.5), t)
    bad = np.zeros((10, 10)); bad[1, 1] = np.nan
    with pytest.raises(ValueError):
        dti_probabilistic(bad, t)
    # NaN outside the scored area (the official 'null or nan outside bounds' encoding) is allowed.
    ok = np.zeros((10, 10)); ok[0, :] = np.nan
    scored = np.ones((10, 10), bool); scored[0, :] = False
    assert np.isfinite(dti_probabilistic(ok, t, scored)["dti"])


def test_official_worked_example_arithmetic():
    """DrivenData problem page (page/967) reports TP=3.00, FP=1.89, FN=2.00 -> TI=0.60."""
    dti = 3.00 / (3.00 + 0.2 * 1.89 + 0.8 * 2.00)
    assert round(dti, 2) == 0.60
