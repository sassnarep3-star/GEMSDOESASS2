#!/usr/bin/env python3
"""EXPERIMENT 1 — emission-geometry study on the shared hide-and-recover holdout.

Question: under the official DW-Tversky metric the false-positive term is
`FP_w = sum_x p(x) * [1 - max_g k(d(x,g))]`, i.e. every predicted pixel lying
*within* the 3 px (300 m) tolerance kernel of a truth pixel costs nothing.
All nine focus-site champions emit isolated single pixels, so their FP mass is
~(number of dots) even when they sit on a real fault.

This experiment measures the score effect of the emission GEOMETRY (collar
distance to the visible catalogue, dilation radius around each emitted pixel,
and a soft taper) on the project's shared, leak-free, spatially-blocked
hide-and-recover holdout (`src/gems_sass2/holdout.py`, evaluator
`GEMSDOE32-HIDE-RECOVER-v3.0`), using hash-pinned champion rasters as parents.

All numbers printed here are HOLDOUT-DTI on the public catalogue proxy.
None of them is an organizer score and none is a projection of one.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, grey_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import evaluate_hide_and_recover, load_holdout_context  # noqa: E402
from gems_sass2.metric import ALPHA, BETA, EPS, kernel  # noqa: E402

DISK = 3.0  # official tolerance radius R = 300 m at 100 m pixel size


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1)
    return np.isfinite(a) & (a > 0)


def dilate_disk(mask: np.ndarray, radius_px: float, n_iter: int = 12) -> np.ndarray:
    """Binary dilation by an approximately-Euclidean disk of the requested radius."""
    if radius_px <= 0:
        return mask.copy()
    size = int(2 * radius_px + 1)
    yy, xx = np.mgrid[-radius_px:radius_px + 1, -radius_px:radius_px + 1]
    footprint = (yy * yy + xx * xx) <= (radius_px + 0.25) ** 2
    out = mask.copy()
    for _ in range(int(n_iter)):
        grown = binary_dilation(out, structure=footprint)
        if grown.sum() == out.sum():
            return grown
        out = grown
    return out


def soft_taper(core: np.ndarray, radius_px: float) -> np.ndarray:
    """p(x) = 1 - d(x, core)/radius clipped at 0 -> graded falloff over the halo."""
    d = distance_transform_edt(~core)
    p = np.clip(1.0 - d / radius_px, 0.0, 1.0).astype(np.float32)
    return p


def evaluate_soft(p: np.ndarray, ctx, b_visible_px: float, name: str) -> dict:
    """Probabilistic holdout score on the fold-censored domain.

    Mirrors `evaluate_hide_and_recover`'s static-raster path but with continuous p:
    per truth pixel g the credit is max over scored pixels of p(x)*k(d(x,g));
    FP mass is sum over scored pixels of p(x)*(1 - max_g k(d(x,g))).
    For p in {0,1} this reduces exactly to the binary evaluator.
    """
    pooled_tp = pooled_fp = pooled_fn = 0.0
    folds = {}
    fp_footprint = dilate_footprint(DISK)
    for cell in ctx.cells:
        sl = cell.bbox
        sub = np.asarray(p[sl], dtype=np.float64)
        active = cell.active_sub & (cell.d_vis_sub > b_visible_px)
        sub = np.where(active, sub, 0.0)
        n_t = cell.n_truth
        k_d = cell.k_dg_sub  # kernel of the (precomputed) distance to the cell truth
        core = sub > 0
        if n_t == 0 or not core.any():
            tp = 0.0
        else:
            # credit per truth pixel = max over scored pixels of p(x)*k(|x-g|):
            # spread each pixel's weighted value over its tolerance disk, then take
            # the per-pixel maximum, then read it off at the truth pixels.
            w = grey_dilation(sub * k_d, footprint=fp_footprint, mode="constant", cval=0.0)
            ty, tx = cell.truth_coords
            tp = float(w[ty, tx].sum())
        fp = float((sub * (1.0 - k_d)).sum())
        fn = float(n_t) - tp
        pooled_tp += tp
        pooled_fp += fp
        pooled_fn += fn
        folds[cell.key] = {
            "dti": float(tp / (tp + ALPHA * fp + BETA * fn + EPS)),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "emitted_mass": float(sub.sum()),
            "emitted_pixels": int(core.sum()),
            "n_truth": n_t,
        }
        fp = float((sub * (1.0 - k_d)).sum())
        fn = float(n_t) - tp
        pooled_tp += tp
        pooled_fp += fp
        pooled_fn += fn
        folds[cell.key] = {
            "dti": float(tp / (tp + ALPHA * fp + BETA * fn + EPS)),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "emitted_mass": float(sub.sum()),
            "emitted_pixels": int(core.sum()),
            "n_truth": n_t,
        }
    score = pooled_tp / (pooled_tp + ALPHA * pooled_fp + BETA * pooled_fn + EPS)
    return {
        "candidate_id": name,
        "score_label": "HOLDOUT-DTI (probabilistic, fold-censored)",
        "pooled_dti": float(score),
        "pooled_tp": pooled_tp,
        "pooled_fp": pooled_fp,
        "pooled_fn": pooled_fn,
        "n_withheld_positives": int(sum(f["n_truth"] for f in folds.values())),
        "folds": folds,
    }


def dilate_footprint(radius_px: float) -> np.ndarray:
    r = int(round(radius_px))
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return ((yy * yy + xx * xx) <= (r + 0.25) ** 2).astype(np.uint8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "official")
    ap.add_argument("--ref", type=Path, default=ROOT / ".cache" / "ref")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "exp1_halo_geometry.json")
    args = ap.parse_args()

    ctx = load_holdout_context(args.data)
    print(f"[holdout] footprint px={int(ctx.foot.sum())} catalogue px={int(ctx.labels.sum())} "
          f"cells={len(ctx.cells)} withheld(px, per-cell sum)={sum(c.n_truth for c in ctx.cells)}",
          flush=True)

    parents = {
        "h19-5-parent-44090": args.ref / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-allfinite.tif",
        "d1-5": args.ref / "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
        "d2-8": args.ref / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-allfinite.tif",
        "lattice-r13-s5": args.ref / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
    }
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "HOLDOUT-DTI (public-catalogue hide-and-recover proxy; NOT an organizer score)",
        "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0 + soft-map variant of the same censoring",
        "parents": {},
        "results": [],
    }

    for name, path in parents.items():
        if not path.is_file():
            print(f"[skip] missing {path}")
            continue
        mask = load_mask(path) & ctx.foot
        report["parents"][name] = {
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "sha256": sha256(path),
            "dots": int(mask.sum()),
            "frac_within_3px_of_catalogue": float(
                (mask & binary_dilation(ctx.labels, iterations=3)).sum() / max(int(mask.sum()), 1)
            ),
        }
        print(f"[parent] {name}: {int(mask.sum())} dots sha={sha256(path)[:12]}", flush=True)
        if int(mask.sum()) == 0:
            continue
        variants = []
        # collar sweep on the binary dots (what the sites did)
        for collar in (0.0, 1.0, 2.0, 3.0, 4.0):
            m = mask.copy()
            if collar > 0:
                m &= ~binary_dilation(ctx.labels, iterations=int(collar))
            res = evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, name=f"{name}|binary|collar{collar}")
            variants.append({
                "kind": "binary_dots", "collar_px": collar, "dilate_px": 0, "soft": False,
                "pixels": int(m.sum()),
                "holdout_dti": res["pooled_dti"], "ci95": res["ci95_cluster_bootstrap"],
                "n_withheld_positives": res["n_withheld_positives"],
            })
            print(f"  [binary collar={collar}] px={int(m.sum())} HOLDOUT-DTI={res['pooled_dti']:.5f} "
                  f"ci={res['ci95_cluster_bootstrap']}", flush=True)
        # dilation of the whole emission (no collar), plus collar+dilation
        for collar in (0.0, 2.0):
            base = mask.copy()
            if collar > 0:
                base &= ~binary_dilation(ctx.labels, iterations=int(collar))
            for rad in (1, 2, 3):
                m = dilate_disk(base, float(rad)) & ctx.foot
                if collar > 0:
                    m &= ~binary_dilation(ctx.labels, iterations=int(collar))
                res = evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, name=f"{name}|dilate{rad}|collar{collar}")
                variants.append({
                    "kind": "binary_dilated", "collar_px": collar, "dilate_px": rad, "soft": False,
                    "pixels": int(m.sum()),
                    "holdout_dti": res["pooled_dti"], "ci95": res["ci95_cluster_bootstrap"],
                    "n_withheld_positives": res["n_withheld_positives"],
                })
                print(f"  [dilate={rad} collar={collar}] px={int(m.sum())} "
                      f"HOLDOUT-DTI={res['pooled_dti']:.5f} ci={res['ci95_cluster_bootstrap']}", flush=True)
            # soft taper over the tolerance disk
            for rad in (3, 4):
                p = soft_taper(base, float(rad))
                res = evaluate_soft(np.nan_to_num(p, nan=0.0), ctx, 0.0, f"{name}|soft{rad}|collar{collar}")
                variants.append({
                    "kind": "soft_taper", "collar_px": collar, "dilate_px": rad, "soft": True,
                    "pixels": int((p > 0).sum()), "mass": float(np.nansum(p)),
                    "holdout_dti": res["pooled_dti"],
                })
                print(f"  [soft taper r={rad} collar={collar}] px={int((p>0).sum())} "
                      f"mass={float(np.nansum(p)):.0f} HOLDOUT-DTI={res['pooled_dti']:.5f}", flush=True)
        report["results"].append({"parent": name, "variants": variants})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(f"[out] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
