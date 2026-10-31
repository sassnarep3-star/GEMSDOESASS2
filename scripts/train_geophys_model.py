#!/usr/bin/env python3
"""Spatially-blocked geophysical fault model (official 19-band stack only).

Design
------
* Inputs are the 83 structural features of `gems_sass2.geophys` (geophysics
  only: no catalogue distance, no label-derived input of any kind).
* Cross-validation is **spatially blocked**: the footprint is cut into
  `--block` x `--block` pixel tiles (200 px = 20 km) and whole tiles are
  assigned to folds.  Neighbouring pixels are never split across train/test,
  so the reported number is a genuine spatial holdout.
* I/O is single-pass sequential.  The feature cube is a 4 GB disk memmap and
  this sandbox has 3 GB of RAM: random-access fancy indexing on the memmap is
  ~1000x slower than streaming whole row tiles, so every stage streams.

Outputs
-------
`.cache/oof.npy`            float32 out-of-fold probability, NaN off coverage
`.cache/model_final.txt`    LightGBM booster trained on every fold
`evidence/geophys_model_cv.json`
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2 import geophys  # noqa: E402

PARAMS = dict(
    objective="binary",
    learning_rate=0.06,
    num_leaves=127,
    min_data_in_leaf=60,
    feature_fraction=0.55,
    bagging_fraction=0.8,
    bagging_freq=1,
    lambda_l2=1.0,
    num_threads=2,
    verbose=-1,
    seed=20261031,
)

TILE_ROWS = 180


def block_ids(shape, block: int) -> np.ndarray:
    h, w = shape
    by = (np.arange(h, dtype=np.int32) // block)
    bx = (np.arange(w, dtype=np.int32) // block)
    return (by[:, None] * (w // block + 2) + bx[None, :]).astype(np.int32)


def iter_tiles(cube: np.memmap, rows: int = TILE_ROWS):
    h = cube.shape[1]
    for r0 in range(0, h, rows):
        r1 = min(r0 + rows, h)
        yield r0, r1, np.asarray(cube[:, r0:r1, :])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--block", type=int, default=200)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--negatives", type=int, default=600_000)
    ap.add_argument("--trees", type=int, default=700)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    if args.quick:
        args.folds, args.negatives, args.trees = 2, 120_000, 120

    import lightgbm as lgb

    t0 = time.time()
    names = geophys.feature_names()
    cube = np.load(ROOT / ".cache" / "features" / "feature_cube.npy", mmap_mode="r")
    assert cube.shape[0] == len(names), cube.shape

    with rasterio.open(ROOT / "data" / "bridge" / "labels.tif") as ds:
        labels = ds.read(1)
    with rasterio.open(geophys.stack_path(ROOT)) as ds:
        coverage = ds.read(1) > geophys.NODATA_SENTINEL
    h, w = coverage.shape
    pos_mask = (labels >= 1) & coverage
    print(f"positives in coverage: {int(pos_mask.sum())}", flush=True)

    blocks = block_ids((h, w), args.block)
    uniq = np.unique(blocks[coverage])
    lut = np.full(int(blocks.max()) + 1, -1, np.int16)
    for i, b in enumerate(uniq):
        lut[b] = i % args.folds
    fold_map = lut[blocks]
    print(f"{len(uniq)} blocks of {args.block}px -> {args.folds} folds "
          f"({time.time() - t0:.0f}s)", flush=True)

    # ---- one streaming pass: draw the training sample --------------------
    rng = np.random.default_rng(20261031)
    neg_cells = coverage & ~pos_mask
    ny_all, nx_all = np.nonzero(neg_cells)
    take = np.sort(rng.choice(ny_all.size, size=min(args.negatives, ny_all.size), replace=False))
    neg_y, neg_x = ny_all[take], nx_all[take]
    del ny_all, nx_all, take, neg_cells
    py, px = np.nonzero(pos_mask)
    sy = np.concatenate([py, neg_y])
    sx = np.concatenate([px, neg_x])
    yy = np.concatenate([np.ones(py.size, np.int8), np.zeros(neg_y.size, np.int8)])
    fb = fold_map[sy, sx]
    del py, px, neg_y, neg_x
    x = np.empty((yy.size, len(names)), np.float32)
    order = np.argsort(sy, kind="stable")
    sy, sx, yy, fb = sy[order], sx[order], yy[order], fb[order]
    del order
    for r0, r1, tile in iter_tiles(cube):
        lo = np.searchsorted(sy, r0, "left")
        hi = np.searchsorted(sy, r1, "left")
        if hi > lo:
            x[lo:hi] = tile[:, sy[lo:hi] - r0, sx[lo:hi]].T
    print(f"training matrix {x.shape} {x.nbytes / 1e6:.0f} MB ({time.time() - t0:.0f}s)", flush=True)

    # ---- spatially blocked CV -------------------------------------------
    oof = np.full((h, w), np.nan, np.float32)
    report = {"block_px": args.block, "folds": args.folds, "negatives": args.negatives,
              "trees": args.trees, "features": len(names), "feature_names": names,
              "folds_report": []}
    boosters = {}
    for f in range(args.folds):
        fit = (fb != f)
        train_blocks = np.unique(blocks[sy[fit], sx[fit]])
        val_lut = np.zeros(int(blocks.max()) + 1, bool)
        val_lut[train_blocks[::10]] = True
        in_val = val_lut[blocks[sy[fit], sx[fit]]]
        idx_fit = np.nonzero(fit)[0]
        idx_tr = idx_fit[~in_val]
        idx_va = idx_fit[in_val]
        dtr = lgb.Dataset(x[idx_tr], label=yy[idx_tr], feature_name=names)
        dva = lgb.Dataset(x[idx_va], label=yy[idx_va], reference=dtr)
        bst = lgb.train(PARAMS, dtr, num_boost_round=args.trees, valid_sets=[dva],
                        callbacks=[lgb.early_stopping(40, verbose=False)])
        boosters[f] = bst
        print(f"  fold {f}: train={idx_tr.size} val={idx_va.size} "
              f"best_iter={bst.best_iteration} ({time.time() - t0:.0f}s)", flush=True)
        del dtr, dva, idx_fit, idx_tr, idx_va, in_val, val_lut

    # ---- one streaming pass: out-of-fold prediction ---------------------
    for r0, r1, tile in iter_tiles(cube):
        flat = tile.reshape(len(names), -1).T
        fm = fold_map[r0:r1].ravel()
        cov = coverage[r0:r1].ravel()
        out = np.full(flat.shape[0], np.nan, np.float32)
        for f in range(args.folds):
            sel = cov & (fm == f)
            if sel.any():
                out[sel] = boosters[f].predict(flat[sel])
        oof[r0:r1] = out.reshape(r1 - r0, w)
        del flat, out
    np.save(ROOT / ".cache" / "oof.npy", oof)
    print(f"OOF written ({time.time() - t0:.0f}s)", flush=True)

    # ---- per-fold metrics on the held-out tiles -------------------------
    for f in range(args.folds):
        cells = coverage & (fold_map == f)
        yt = (labels[cells] >= 1).astype(np.int8)
        pr = oof[cells]
        ok = bool(np.isfinite(pr).any()) and (yt.min() != yt.max())
        auc = float(roc_auc_score(yt, pr)) if ok else float("nan")
        apv = float(average_precision_score(yt, pr)) if ok else float("nan")
        report["folds_report"].append({"fold": f, "n_test": int(cells.sum()),
                                       "pos": int(yt.sum()), "auc": auc, "ap": apv,
                                       "best_iteration": int(boosters[f].best_iteration or 0)})
        print(f"  fold {f}: n={int(cells.sum())} pos={int(yt.sum())} AUC={auc:.4f} AP={apv:.4f}",
              flush=True)

    aucs = [r["auc"] for r in report["folds_report"] if np.isfinite(r["auc"])]
    report["auc_mean"] = float(np.mean(aucs)) if aucs else None
    report["auc_min"] = float(np.min(aucs)) if aucs else None
    report["wall_seconds"] = round(time.time() - t0, 1)

    # ---- final model on all sampled rows --------------------------------
    dall = lgb.Dataset(x, label=yy, feature_name=names)
    n_rounds = int(np.mean([r["best_iteration"] for r in report["folds_report"]])) or args.trees
    final = lgb.train(PARAMS, dall, num_boost_round=n_rounds)
    final.save_model(str(ROOT / ".cache" / "model_final.txt"))
    imp = sorted(zip(names, final.feature_importance("gain")), key=lambda t: -t[1])
    report["top_features"] = [{"feature": n, "gain": float(g)} for n, g in imp[:30]]
    report["final_rounds"] = n_rounds
    (ROOT / "evidence" / "geophys_model_cv.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps({k: report[k] for k in ("auc_mean", "auc_min", "wall_seconds")}, indent=1))
    print("top:", [n for n, _ in imp[:10]], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
