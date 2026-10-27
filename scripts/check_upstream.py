#!/usr/bin/env python3
"""Run synthetic correctness probes against the actual shared GEMSDOE32 tools.

No fork or patch is created. These are unit probes, not geological experiments.
Specify a trusted local template checkout; unknown interfaces fail closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(root: Path) -> dict:
    sys.path.insert(0, str(root / "src"))
    from gems32 import holdout, release_gate  # type: ignore[import-not-found]

    rng = np.random.default_rng(27)
    surface, peer = rng.random((16, 16)), rng.random((16, 16))
    foot = np.ones((16, 16), dtype=bool)
    dots = np.zeros((16, 16), dtype=bool)
    dots[4, 4] = dots[11, 11] = True
    result = release_gate.compare_registry(surface, dots, foot, {"peer": (peer, dots)}, stage="surface")
    comparison = result["comparisons"][0]

    cells = []
    preds = {}
    for seed in (20, 21):
        for fold in range(4):
            key = f"draw{seed}_fold{fold}"
            is_empty = seed == 20 and fold == 0
            empty_coords = (np.array([], dtype=int), np.array([], dtype=int))
            truth = empty_coords if is_empty else (np.array([8]), np.array([8]))
            cells.append(holdout.PreparedCell(
                key=key, fold=fold, seed=seed, bbox=(slice(0, 16), slice(0, 16)),
                active_sub=foot, truth_coords=truth, k_dg_sub=np.zeros_like(surface),
                n_truth=0 if is_empty else 1,
            ))
            arr = np.zeros_like(foot)
            if is_empty:
                arr[4, 4] = True
            preds[key] = arr
    out = holdout.evaluate_hide_and_recover(preds, SimpleNamespace(foot=foot, cells=cells), grid_n=4, n_boot=20)
    recorded_fold_fp = sum(c["fp"] for c in out["folds"].values())
    pooled_fp = float(out["_block_totals"][1].sum())
    surface_pass_correct = comparison["within_3px_fraction"] == 1.0 and result["passed"] is False
    fp_accounting_correct = recorded_fold_fp == pooled_fp == 1.0
    return {
        "probe_type": "synthetic unit checks; no geological holdout performed",
        "files": {"release_gate_sha256": digest(root / "src/gems32/release_gate.py"),
                  "holdout_sha256": digest(root / "src/gems32/holdout.py")},
        "surface_duplicate": {
            "within_3px_fraction": comparison["within_3px_fraction"],
            "rank_correlation": comparison["spearman"],
            "observed_passed": result["passed"],
            "expected_passed": False,
            "correct": surface_pass_correct,
            "issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/42",
        },
        "zero_truth_false_positive_accounting": {
            "fold_fp_sum": recorded_fold_fp, "pooled_fp_sum": pooled_fp,
            "expected_fp_sum": 1.0, "correct": fp_accounting_correct,
            "issue": "https://github.com/buffedlizard55-lab/GEMSDOE32/issues/41",
        },
        "ready_for_shared_holdout": bool(surface_pass_correct and fp_accounting_correct),
        "action": "Fix upstream once and rerun these probes; do not maintain a private evaluator fork.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = probe(args.template_root.resolve())
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if result["ready_for_shared_holdout"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
