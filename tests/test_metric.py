import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gems.metric import dti_binary, tri_kernel


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
