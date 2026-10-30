#!/usr/bin/env python3
"""EXPERIMENT 2 — detached scarp-continuity detector + emission-rule study.

Hypothesis under test (H-SC-1, "blind-tip scarp continuation"):
    Undocumented Quaternary faults in the competition truth set concentrate where a
    LiDAR-visible scarp lineament (a) has high local scarp amplitude, (b) is linearly
    continuous over several hundred metres, and (c) extends a mapped catalogue strand
    along strike beyond its traced tip (blind tip-zone continuation) while remaining
    detached from the mapped trace itself.

Differences from the nine focus sites and from this repository's earlier lanes:
    * catalogue-geometry *extension* features (a tip/step-over corridor derived from
      the visible faults only) are used as predictors; the focus sites use the
      catalogue only as a collar that *excludes* pixels;
    * scarp evidence is a ridge-linearity/continuity transform of the 2 m LiDAR band
      stack, not a single scarp or ridge amplitude;
    * training is fold-aware (visible catalogue only) and every candidate surface is
      scored on the shared hide-and-recover holdout before any emission is written.

All numbers printed are HOLDOUT-DTI on the public-catalogue proxy
(evaluator GEMSDOE32-HIDE-RECOVER-v3.0). They are not organizer scores, and no
leaderboard value is inferred from them.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    HIDE_RECOVER_EVALUATOR_VERSION,
    evaluate_hide_and_recover,
    evaluate_sgmc_with_ci,
    load_holdout_context,
)

LIDAR = ROOT / "data" / "external" / "lidar_scarp_features_u8.tif"
RAD = ROOT / "data" / "external" / "geodawn_rad_u8.tif"
STACK = ROOT / "data" / "official" / "training_features.tif"
VENTS = ROOT / ".cache" / "ext" / "gdr_volcanic_vents_in_footprint.csv"
SHAPE = (3730, 3292)
STACK_BANDS = {4: "geod_2ndinv", 15: "depth_to_base_surf", 12: "det_elev", 19: "det_elev_slope"}


def band(path: Path, index: int) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(index).astype(np.float32)


def build_features(foot: np.ndarray) -> tuple[dict[str, np.ndarray], list[str]]:
    """Static (catalogue-independent) predictor stack, flattened to footprint pixels."""
    ex = band(LIDAR, 1)
    step = band(LIDAR, 3)
    lapneg = band(LIDAR, 4)
    lappos = band(LIDAR, 5)
    down = band(LIDAR, 6)
    up = band(LIDAR, 7)
    cross = band(LIDAR, 8)
    relief = band(LIDAR, 9)
    coh = band(LIDAR, 10)

    amp = np.maximum.reduce([ex, step, up, down])
    ridge_short = ndi.maximum_filter(amp, size=3)
    continuity = ndi.maximum_filter(ridge_short, size=11) - ndi.minimum_filter(ridge_short, size=11)
    localmax = ridge_short - ndi.minimum_filter(amp, size=3)
    dipole = np.minimum(lapneg, lappos)
    channel = cross - np.maximum(up, down)
    lin = 255.0 - np.abs(cross - np.maximum(up, down))

    k, th, u, tc = (band(RAD, i) for i in (1, 2, 3, 4))
    g = lambda a: np.abs(np.gradient(a, axis=1)) + np.abs(np.gradient(a, axis=0))  # noqa: E731
    thk = th * 255.0 / np.maximum(k, 1.0)
    rad_grad = np.maximum.reduce([g(k), g(th), g(tc)])
    rad_thk_edge = ndi.maximum_filter(thk, size=3) - ndi.minimum_filter(thk, size=3)
    rad_u_th = np.abs(th - u)

    if VENTS.is_file():
        seeds = np.zeros(SHAPE, bool)
        for line in VENTS.read_text().splitlines()[1:]:
            parts = line.split(",")
            try:
                r, c = int(float(parts[3])), int(float(parts[4]))
            except (ValueError, IndexError):
                continue
            if 0 <= r < SHAPE[0] and 0 <= c < SHAPE[1]:
                seeds[r, c] = True
        vent = ndi.distance_transform_edt(~seeds).astype(np.float32) if seeds.any() else None
    else:
        vent = None

    feats = {"s_amp": amp, "s_continuity": continuity, "s_localmax": localmax,
             "s_dipole": dipole, "s_channel": channel, "s_lin": lin, "s_relief": relief,
             "s_coh": coh, "s_lapneg": lapneg, "rad_grad": rad_grad,
             "rad_thk_edge": rad_thk_edge, "rad_u_th": rad_u_th}
    if vent is not None:
        feats["vent_dist"] = vent
    with rasterio.open(STACK) as src:
        for index, name in STACK_BANDS.items():
            a = src.read(index).astype(np.float32)
            a[(~np.isfinite(a)) | (np.abs(a) > 1e30)] = 0.0
            feats["x_" + name] = a
            del a
    names = list(feats)
    fp = np.flatnonzero(foot.ravel())
    # raster pixel index -> column in S (footprint rank)
    rank = np.full(foot.size, -1, np.int64)
    rank[fp] = np.arange(fp.size)
    bundle_extra = {"rank": rank}
    S = np.empty((len(feats), fp.size), np.float32)
    for i, (k, f) in enumerate(feats.items()):
        S[i] = f.ravel()[fp]
        feats[k] = None
    del feats
    return {"S": S, "fp": fp, **bundle_extra}, names


def catalogue_features(visible: np.ndarray, foot: np.ndarray) -> dict[str, np.ndarray]:
    """Fold-local catalogue geometry: halo distance, blind-tip corridor, orientation."""
    d = ndi.distance_transform_edt(~visible).astype(np.float32)
    halo = ((d > 2) & (d <= 9)).astype(np.float32)
    comp, n = ndi.label(visible, structure=np.ones((3, 3), int))
    tip = np.zeros(SHAPE, bool)
    if n:
        sizes = np.bincount(comp.ravel())
        er = ndi.binary_erosion(visible)
        ends = visible & ~ndi.binary_dilation(er, iterations=2)
        # endpoint neighbourhood: pixels 3..10 px from a trace endpoint
        de = ndi.distance_transform_edt(~ends)
        tip = (de > 3) & (de <= 10) & halo.astype(bool)
    return {"cat_dist": d, "cat_halo": halo, "cat_tip": tip.astype(np.float32)}


def auc_from_scores(y: np.ndarray, s: np.ndarray) -> float:
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(s.size, dtype=np.float64)
    ranks[order] = np.arange(s.size)
    n_pos = int(y.sum())
    n_neg = s.size - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    return float((ranks[y == 1].sum() - n_pos * (n_pos - 1) / 2) / (n_pos * n_neg))


def cell_of_max_thinning(score: np.ndarray, foot: np.ndarray, sep_px: float, n_dots: int,
                         collar_px: float, labels: np.ndarray) -> np.ndarray:
    """Keep the best-scoring pixel per sep_px grid cell (documented approximation of
    Poisson-disk separation: realised spacing >= sep_px/sqrt(2))."""
    s = np.where(foot, score, -1.0).astype(np.float32)
    if collar_px > 0:
        s = np.where(ndi.binary_dilation(labels, iterations=int(collar_px)), -1.0, s)
    flat = s.ravel()
    cand = np.flatnonzero(flat > 0)
    if cand.size == 0:
        return np.zeros(s.shape, bool)
    h, w = s.shape
    cy, cx = np.divmod(cand, w)
    cell = max(int(round(sep_px)), 1)
    key = (cy // cell) * (w // cell + 2) + (cx // cell)
    order = np.lexsort((cand, key, -flat[cand]))
    ks = key[order]
    first = np.concatenate(([True], ks[1:] != ks[:-1]))
    # NOTE: `order` indexes INTO `cand`; it is not a pixel index. The previous
    # version used it directly to set the mask, which emitted the wrong pixels
    # (found 2026-10-30, see IRREGULARITIES.md IR-VRC-01).
    chosen = cand[order[first][:n_dots]]
    mask = np.zeros(h * w, bool)
    mask[chosen] = True
    return mask.reshape(h, w) & foot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "official")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "exp2_scarp_continuity.json")
    ap.add_argument("--neg-stride", type=int, default=80)
    ap.add_argument("--quick", action="store_true", help="4 cells instead of 8")
    args = ap.parse_args()

    t0 = datetime.now(timezone.utc)
    ctx = load_holdout_context(args.data)
    foot, labels = ctx.foot, ctx.labels
    cells = ctx.cells[:4] if args.quick else ctx.cells
    print(f"[holdout] cells={len(cells)} withheld={sum(c.n_truth for c in cells)}", flush=True)

    print("[feat] building static predictor stack", flush=True)
    bundle, static_names = build_features(foot)
    S, fp, rank = bundle["S"], bundle["fp"], bundle["rank"]
    all_names = static_names + ["cat_halo", "cat_tip", "log_cat_dist"]
    print(f"[feat] {S.shape[0]} static + 3 catalogue features; {fp.size} footprint pixels", flush=True)

    def gather(cat: dict[str, np.ndarray], pix: np.ndarray) -> np.ndarray:
        """pix are *raster* pixel indices; returns the design matrix."""
        col = rank[pix]
        bad = int((col < 0).sum())
        if bad:
            raise RuntimeError(f"{bad} sampled pixels are outside the footprint")
        X = np.empty((pix.size, len(all_names)), np.float32)
        X[:, :S.shape[0]] = S[:, col].T
        X[:, S.shape[0]] = cat["cat_halo"].ravel()[pix]
        X[:, S.shape[0] + 1] = cat["cat_tip"].ravel()[pix]
        X[:, S.shape[0] + 2] = np.log1p(cat["cat_dist"].ravel()[pix])
        return X

    pos_in_foot = np.cumsum(foot.ravel()) - 1
    truth_2d = np.zeros(foot.shape, bool)
    domain_2d = np.zeros(foot.shape, bool)
    for c in cells:
        sl = c.bbox
        domain_2d[sl] |= c.active_sub
        ty, tx = c.truth_coords
        truth_2d[ty + sl[0].start, tx + sl[1].start] = True
    domain_2d &= foot
    truth_2d &= domain_2d

    # ---- leakage canary (protocol rule 4): each feature alone ------------------
    cat_static = catalogue_features(labels, foot)
    dom_pix = np.flatnonzero(domain_2d.ravel())
    sub = dom_pix[::7]
    y_sub = truth_2d.ravel()[sub].astype(int)
    Xcan = gather(cat_static, sub)
    canary = []
    for j, nm in enumerate(all_names):
        a = auc_from_scores(y_sub, Xcan[:, j])
        canary.append({"feature": nm, "auc": round(max(a, 1 - a), 5),
                       "catalogue_derived": nm.startswith("cat_") or nm == "log_cat_dist"})
    worst_real = max((r for r in canary if not r["catalogue_derived"]), key=lambda r: r["auc"])
    worst_any = max(canary, key=lambda r: r["auc"])
    print(f"[canary] worst non-catalogue AUC={worst_real['auc']} ({worst_real['feature']}); "
          f"worst overall={worst_any['auc']} ({worst_any['feature']})", flush=True)
    del Xcan

    # ---- fold-aware training, out-of-fold propensity ----------------------------
    surf = np.zeros(foot.shape, dtype=np.float32)
    coef_rows: list[dict] = []
    for c in cells:
        sl = c.bbox
        visible = c.visible_full
        cat = catalogue_features(visible, foot)
        # Leak-free LOQO pool: every pixel outside this cell's test quadrant and
        # outside its 1.5 km collar. Because a component that touches the collar is
        # hidden from training *and* excluded from the test domain, no fault can be a
        # training positive and a test positive at the same time.
        outside = foot & ~ctx.collars[c.fold]
        train_ok = outside & (cat["cat_dist"] > 2)
        pos_pix = np.flatnonzero((train_ok & ctx.labels).ravel())
        neg_pix = np.flatnonzero((train_ok & ~ndi.binary_dilation(ctx.labels, iterations=2)).ravel())[:: args.neg_stride]
        tr = np.concatenate([pos_pix, neg_pix])
        Xtr = gather(cat, tr)
        ytr = np.concatenate([np.ones(pos_pix.size, int), np.zeros(neg_pix.size, int)])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        clf = LogisticRegression(max_iter=500, C=1.0)
        clf.fit((Xtr - mu) / sd, ytr)
        coef_rows.append({"cell": c.key, "n_pos": int(pos_pix.size), "n_neg": int(neg_pix.size),
                          "coefs": {n: round(float(v), 3) for n, v in zip(all_names, clf.coef_[0])}})
        active = c.active_sub & foot[sl]            # test domain: eroded quadrant minus visible faults
        gy, gx = np.mgrid[sl[0].start:sl[0].stop, sl[1].start:sl[1].stop]
        gpid = (gy * foot.shape[1] + gx).ravel()
        act_gp = gpid[np.flatnonzero(active.ravel())]
        Xte = gather(cat, act_gp)
        p = clf.predict_proba((Xte - mu) / sd)[:, 1].astype(np.float32)
        surf.ravel()[act_gp] = p
        print(f"[fold] {c.key}: pos={pos_pix.size} neg={neg_pix.size} "
              f">0.5 px={int((p > 0.5).sum())}", flush=True)
        del Xtr, Xte

    np.save(ROOT / ".cache" / "surf_learned.npy", surf)
    amp_surface = np.zeros(foot.shape, np.float32)
    amp_surface.ravel()[np.flatnonzero(foot.ravel())] = S[0]
    amp_surface /= 255.0

    results = []
    for label, surface in (("learned_scarp_continuity", surf), ("scarp_amp_control", amp_surface)):
        for cfg in ({"sep_px": 2.8, "collar_px": 2.0, "n_dots": 37654},
                    {"sep_px": 2.8, "collar_px": 0.0, "n_dots": 37654},
                    {"sep_px": 2.8, "collar_px": 2.0, "n_dots": 44090},
                    {"sep_px": 1.5, "collar_px": 2.0, "n_dots": 70000},
                    {"sep_px": 5.0, "collar_px": 2.0, "n_dots": 37654}):
            m = cell_of_max_thinning(surface, foot, cfg["sep_px"], cfg["n_dots"],
                                     cfg["collar_px"], labels)
            res = evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, name=f"{label}|{cfg}")
            sg = evaluate_sgmc_with_ci(m, ctx, name=f"{label}|{cfg}|sgmc")
            row = {"surface": label, **cfg, "dots": int(m.sum()),
                   "holdout_dti": res["pooled_dti"], "ci95": res["ci95_cluster_bootstrap"],
                   "n_withheld_positives": res["n_withheld_positives"],
                   "detached_600m_dti": res["detached_600m"]["pooled_dti"],
                   "sgmc_offcat_raw_dti": sg["sgmc_raw_pooled_dti"],
                   "sgmc_n_truth": sg["n_withheld_positives"]}
            results.append(row)
            print(f"[eval] {label} {json.dumps(cfg)} dots={row['dots']} "
                  f"HOLDOUT-DTI={row['holdout_dti']:.5f} CI={np.round(row['ci95'],5).tolist()} "
                  f"detached={row['detached_600m_dti']:.5f} SGMC-offcat={row['sgmc_offcat_raw_dti']:.5f}",
                  flush=True)

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": round((datetime.now(timezone.utc) - t0).total_seconds(), 1),
        "evidence_class": "HOLDOUT-DTI (public-catalogue hide-and-recover proxy); NOT an organizer score",
        "evaluator_version": HIDE_RECOVER_EVALUATOR_VERSION,
        "quick": bool(args.quick),
        "hypothesis": "H-SC-1 blind-tip scarp continuation",
        "features": all_names,
        "leakage_canary": {"worst_non_catalogue": worst_real, "worst_any": worst_any,
                           "threshold": 0.90, "all": canary,
                           "note": "log_cat_dist / cat_halo are catalogue-derived and are "
                                   "reported for transparency; they are fold-local in the model."},
        "folds": coef_rows,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"[out] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
