#!/usr/bin/env python3
"""Paired cluster bootstrap for the STRAIN-RIDGE holdout advantage.

Both the candidate and the incumbent-family control are scored against the same
withheld truth, so the *ratio* of their DTI is far better determined than either
absolute value.  Resampling units are the withheld spatial blocks (29 of 144 at
the pre-registered 20 % fraction), which preserves spatial correlation.

Emits ``evidence/strain_ridge_ci.json``.
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
sys.path.insert(0, str(ROOT / "scripts"))

from gems.metric import dti_probabilistic  # noqa: E402
from holdout_strain_ridge import (  # noqa: E402
    HOLDOUT_FRACTION, N_BLOCKS, SEED, rasterise_qfaults,
)
from gems_sass2.strain_ridge import (  # noqa: E402
    COLLAR_PX, MIN_SEP_PX, build_prior, greedy_dots,
)

ALPHA, BETA, R = 0.2, 0.8, 3.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cube", required=True, type=pathlib.Path)
    ap.add_argument("--shp", required=True, type=pathlib.Path)
    ap.add_argument("--sample", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--n-dots", type=int, default=35_000)
    ap.add_argument("--n-boot", type=int, default=4000)
    args = ap.parse_args()

    cube = dict(np.load(args.cube))
    with rasterio.open(args.sample) as ds:
        foot = np.isfinite(ds.read(1))
        h, w = ds.height, ds.width

    draw, bid, nf = rasterise_qfaults(args.shp, args.sample)
    rng = np.random.default_rng(SEED)
    order = np.arange(N_BLOCKS * N_BLOCKS)
    rng.shuffle(order)
    held = sorted(int(b) for b in order[: int(round(HOLDOUT_FRACTION * N_BLOCKS ** 2))])
    hidden = [i for i in range(nf) if int(bid[i]) in held]
    visible = [i for i in range(nf) if int(bid[i]) not in held]
    truth = draw(hidden) & foot
    vis = draw(visible) & foot

    prior = build_prior(cube)
    allowed = foot & (ndi.distance_transform_edt(~vis) > COLLAR_PX)
    dots = greedy_dots(prior, allowed, args.n_dots, MIN_SEP_PX)

    g = np.random.default_rng(7)
    cand_cells = np.flatnonzero(allowed.ravel())
    g.shuffle(cand_cells)
    occ = np.zeros((h, w), bool)
    rad = int(np.ceil(MIN_SEP_PX / 2))
    keep = []
    for i in cand_cells:
        r, c = divmod(int(i), w)
        if occ[max(0, r - rad):r + rad + 1, max(0, c - rad):c + rad + 1].any():
            continue
        occ[r, c] = True
        keep.append(int(i))
        if len(keep) >= args.n_dots:
            break
    uniform = np.asarray(keep, np.int64)

    def block_of(rr, cc):
        return (np.clip((rr / h * N_BLOCKS).astype(int), 0, N_BLOCKS - 1) * N_BLOCKS
                + np.clip((cc / w * N_BLOCKS).astype(int), 0, N_BLOCKS - 1))

    def terms(idx):
        p = np.zeros(h * w, np.float32)
        p[idx] = 1.0
        p = p.reshape(h, w)
        r = dti_probabilistic(p, truth, score_mask=foot)
        dg = ndi.distance_transform_edt(~truth)
        f = p * (1.0 - np.clip(1.0 - dg / R, 0, 1))
        rows, cols = np.nonzero(truth)
        best = np.zeros(rows.size)
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                d = float(np.hypot(dx, dy))
                if d > R:
                    continue
                r2, c2 = rows + dy, cols + dx
                ok = (r2 >= 0) & (r2 < h) & (c2 >= 0) & (c2 < w)
                v = np.zeros(rows.size)
                v[ok] = p[r2[ok], c2[ok]] * (1.0 - d / R)
                np.maximum(best, v, out=best)
        tb = block_of(rows, cols)
        pr, pc = np.nonzero(f > 0)
        fv, fb = f[pr, pc], block_of(pr, pc)
        return {
            "dti": float(r["dti"]), "TPw": float(r["TP"]), "FPw": float(r["FP"]),
            "FNw": float(r["FN"]),
            "bT": {b: float(best[tb == b].sum()) for b in held},
            "bG": {b: int((tb == b).sum()) for b in held},
            "bF": {b: float(fv[fb == b].sum()) for b in held},
            "FP_out": float(fv[~np.isin(fb, held)].sum()),
        }

    c, u = terms(dots), terms(uniform)

    def boot(t):
        rr = np.random.default_rng(7)
        out = []
        for _ in range(args.n_boot):
            pk = rr.choice(held, len(held), replace=True)
            tp = sum(t["bT"][b] for b in pk)
            fp = t["FP_out"] + sum(t["bF"][b] for b in pk)
            gg = sum(t["bG"][b] for b in pk)
            den = tp + ALPHA * fp + BETA * (gg - tp)
            out.append(tp / den if den > 0 else 0.0)
        return np.asarray(out)

    bc, bu = boot(c), boot(u)
    rat = np.divide(bc, bu, out=np.full_like(bc, np.nan), where=bu > 0)
    rat = rat[np.isfinite(rat)]

    out = {
        "n_dots": int(dots.size),
        "holdout_dti": c["dti"],
        "uniform_control_dti": u["dti"],
        "ratio": c["dti"] / u["dti"],
        "holdout_dti_ci95": [float(np.percentile(bc, 2.5)), float(np.percentile(bc, 97.5))],
        "uniform_control_ci95": [float(np.percentile(bu, 2.5)), float(np.percentile(bu, 97.5))],
        "ratio_ci95": [float(np.percentile(rat, 2.5)), float(np.percentile(rat, 97.5))],
        "prob_ratio_gt_1": float((rat > 1.0).mean()),
        "withheld_positive_cells": int(truth.sum()),
        "blocks_held": len(held), "blocks_total": N_BLOCKS * N_BLOCKS,
        "bootstrap": f"paired cluster bootstrap over {len(held)} withheld spatial blocks, "
                     f"{args.n_boot} draws",
        "evaluator": "gems.metric.dti_probabilistic alpha=0.2 beta=0.8 R=300 m; whole footprint",
        "label": ("HOLDOUT-DTI (mapped USGS/INGENIOUS traces withheld by spatial block) "
                  "— NOT a leaderboard score and NOT organizer-confirmed"),
        "caveat": ("The truth is mapped fault traces, not the hidden expert-identified new faults. "
                   "The ratio measures relative placement quality, not a leaderboard gain."),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
