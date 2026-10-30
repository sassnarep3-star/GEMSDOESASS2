#!/usr/bin/env python3
"""Spatially-blocked hide-and-recover holdout for the STRAIN-RIDGE prior.

Protocol (pre-registered)
-------------------------
1. Partition the competition grid into a 6x6 lattice of blocks.  Every official
   USGS/INGENIOUS fault *feature* is assigned to the block containing its
   centroid.  Seven blocks (19.4 %) are withheld whole, so no held-out trace
   crosses a block boundary un-hidden.
2. Truth  = the withheld traces, rasterised as 1-cell lines (``Hid``).
   Visible = the remaining traces; **only** ``Visible`` may be used to build the
   collar mask, so no catalogue information leaks into the placement.
3. Every prior is built from geophysical layers only (strain / seismicity /
   LiDAR scarp stack).  A single-feature AUC canary is run on the truth; any
   feature above 0.90 is leakage until disproved.
4. Score with the shared exact distance-weighted Tversky evaluator
   (``gems.metric.dti_probabilistic``, alpha 0.2, beta 0.8, 300 m triangular).

Reported numbers are HOLDOUT-DTI against mapped fault traces — **not**
leaderboard scores and not organiser-confirmed.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.metric import dti_probabilistic  # noqa: E402
from gems_sass2.strain_ridge import (  # noqa: E402
    COLLAR_PX,
    MIN_SEP_PX,
    build_prior,
    composite,
    greedy_dots,
    zscore,
)

N_BLOCKS = 12
HOLDOUT_FRACTION = 0.20
SEED = 20261030


def rasterise_qfaults(shp: pathlib.Path, sample: pathlib.Path):
    """Return (all_features, block_id_per_feature, block_grid_shape)."""
    import shapefile
    from pyproj import Transformer
    from rasterio.features import rasterize
    from shapely.geometry import LineString

    src_crs = ("+proj=aea +lat_0=23 +lon_0=-117 +lat_1=29.5 +lat_2=45.5 "
               "+x_0=0 +y_0=0 +datum=NAD83 +units=m")
    with rasterio.open(sample) as ds:
        transform, shape = ds.transform, (ds.height, ds.width)
        left, top = transform.c, transform.f
        right, bottom = left + shape[1] * transform.a, top + shape[0] * transform.e
    tr = Transformer.from_crs(src_crs, "EPSG:32611", always_xy=True)

    geoms, blocks = [], []
    for sr in shapefile.Reader(str(shp)).iterShapeRecords():
        pts = sr.shape.points
        if len(pts) < 2:
            continue
        x, y = tr.transform(*np.asarray(pts, dtype=np.float64).T)
        if x.max() < left or x.min() > right or y.max() < bottom or y.min() > top:
            continue
        geoms.append(LineString(np.column_stack([x, y])))
        cx = float(np.clip(x.mean(), left, right - 1e-6))
        cy = float(np.clip(y.mean(), bottom, top - 1e-6))
        col = int((cx - left) / (right - left) * N_BLOCKS)
        row = int((top - cy) / (top - bottom) * N_BLOCKS)
        blocks.append(row * N_BLOCKS + col)

    def draw(idx):
        if not idx:
            return np.zeros(shape, dtype=bool)
        return rasterize([(geoms[i], 1) for i in idx], out_shape=shape,
                         transform=transform, fill=0, dtype="uint8").astype(bool)

    return draw, np.asarray(blocks), len(geoms)


def dti(pred: np.ndarray, truth: np.ndarray, footprint: np.ndarray) -> dict:
    r = dti_probabilistic(np.asarray(pred, np.float64), truth, score_mask=footprint)
    return {"holdout_dti": r["dti"], "TPw": r["TP"], "FPw": r["FP"], "FNw": r["FN"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cube", required=True, type=pathlib.Path)
    ap.add_argument("--shp", required=True, type=pathlib.Path)
    ap.add_argument("--sample", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--n-dots", type=int, nargs="+", default=[20000, 35000, 50000, 70000])
    args = ap.parse_args()

    cube = dict(np.load(args.cube))
    with rasterio.open(args.sample) as ds:
        footprint = np.isfinite(ds.read(1))
        shape = (ds.height, ds.width)

    draw, block_id, n_feat = rasterise_qfaults(args.shp, args.sample)
    rng = np.random.default_rng(SEED)
    order = np.arange(N_BLOCKS * N_BLOCKS)
    rng.shuffle(order)
    held = set(int(b) for b in order[: int(round(HOLDOUT_FRACTION * N_BLOCKS ** 2))])
    hidden_idx = [i for i in range(n_feat) if int(block_id[i]) in held]
    visible_idx = [i for i in range(n_feat) if int(block_id[i]) not in held]

    truth = draw(hidden_idx) & footprint
    visible = draw(visible_idx) & footprint

    # Evaluation mask = the withheld blocks only.  Predicting outside a held-out
    # block cannot be credited (no truth exists there), so scoring is confined to
    # the region that is actually being tested -- the standard spatial holdout.
    eval_mask = np.zeros(shape, bool)
    ev_blocks = set(int(b) for b in held)
    for i in range(n_feat):
        if int(block_id[i]) in ev_blocks:
            eval_mask |= draw([i])
    if truth.sum() == 0:
        raise SystemExit("empty holdout truth")

    # ---- leakage canary ---------------------------------------------------
    bg = rng.choice(np.flatnonzero((footprint & ~visible).ravel()), 40000, replace=False)
    pos = np.flatnonzero(truth.ravel())
    if pos.size > 15000:
        pos = rng.choice(pos, 15000, replace=False)
    from sklearn.metrics import roc_auc_score
    canary = {}
    for k, v in cube.items():
        s = np.r_[v.ravel()[pos], v.ravel()[bg]]
        ok = np.isfinite(s)
        if ok.sum() < 0.5 * s.size:
            continue
        canary[k] = float(roc_auc_score(np.r_[np.ones(pos.size), np.zeros(bg.size)][ok], s[ok]))

    # ---- placement --------------------------------------------------------
    prior = build_prior(cube)
    d_vis = ndi.distance_transform_edt(~visible)
    allowed = footprint & (d_vis > COLLAR_PX)

    def emit(idx):
        out = np.zeros(shape[0] * shape[1], np.float32)
        out[idx] = 1.0
        return out.reshape(shape)

    def score(pred, mask):
        return dti(pred, truth, mask)

    def uniform(n, seed=7):
        """Incumbent-family control: uniform blue-noise sample, same allowed set."""
        g = np.random.default_rng(seed)
        cand = np.flatnonzero(allowed.ravel())
        g.shuffle(cand)
        occ = np.zeros(shape, bool)
        keep = []
        rad = int(np.ceil(MIN_SEP_PX / 2))
        for i in cand:
            r, c = divmod(int(i), shape[1])
            if occ[max(0, r - rad):r + rad + 1, max(0, c - rad):c + rad + 1].any():
                continue
            occ[r, c] = True
            keep.append(int(i))
            if len(keep) >= n:
                break
        return np.asarray(keep, np.int64)

    rows = []
    for n in args.n_dots:
        cand = greedy_dots(prior, allowed, n, MIN_SEP_PX)
        uni = emit(uniform(n))
        block_c, block_u = score(emit(cand), eval_mask), score(uni, eval_mask)
        glob_c, glob_u = score(emit(cand), footprint), score(uni, footprint)
        rows.append({
            "n_dots": int(cand.size),
            "within_withheld_blocks": {
                "strain_ridge": block_c, "uniform_lattice_control": block_u,
                "ratio_vs_uniform": (block_c["holdout_dti"] / block_u["holdout_dti"]
                                     if block_u["holdout_dti"] > 0 else None),
            },
            "whole_footprint": {
                "strain_ridge": glob_c, "uniform_lattice_control": glob_u,
                "ratio_vs_uniform": (glob_c["holdout_dti"] / glob_u["holdout_dti"]
                                     if glob_u["holdout_dti"] > 0 else None),
            },
        })
        print(f"  N={n:6d}  blocks: ridge={block_c['holdout_dti']:.4f}"
              f" uni={block_u['holdout_dti']:.4f} | footprint: ridge={glob_c['holdout_dti']:.4f}"
              f" uni={glob_u['holdout_dti']:.4f}")

    receipt = {
        "protocol": {
            "evaluator": "gems.metric.dti_probabilistic (alpha 0.2, beta 0.8, R=300 m)",
            "block_grid": [N_BLOCKS, N_BLOCKS],
            "blocks_held_out": sorted(held),
            "holdout_fraction": HOLDOUT_FRACTION,
            "seed": SEED,
            "withheld_positive_cells": int(truth.sum()),
            "evaluation_masks": ["within withheld blocks only (7 of 36 blocks)", "whole competition footprint"],
            "evaluation_cells": int(eval_mask.sum()),
            "visible_positive_cells": int(visible.sum()),
            "collar_px": COLLAR_PX,
            "min_sep_px": MIN_SEP_PX,
            "truth_source": "USGS Quaternary Faults + GBCGE INGENIOUS (qfaults_ingenious 2023-06-27)",
        },
        "leakage_canary_single_feature_auc": dict(
            sorted(canary.items(), key=lambda kv: -abs(kv[1] - 0.5))[:15]
        ),
        "canary_max_auc": max((abs(v - 0.5) + 0.5 for v in canary.values()), default=None),
        "results": rows,
        "label": "HOLDOUT-DTI — mapped fault traces, not the hidden competition truth",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
