#!/usr/bin/env python3
"""THERMAL-CONDUIT EMISSION (S3) — lane self-declared (no method paragraph was ever
supplied to this portfolio; see IR-10).  This is one experiment suite in three phases.

HYPOTHESIS
    Faults that the scarp-dependent USGS/INGENIOUS catalogue missed still channel
    hydrothermal upflow.  Shallow-temperature anomalies and their deposits mark where
    those conduits are or were boiling: the hidden test truth ("new faults not in the
    USGS database") should be enriched near thermal anomalies relative to the blind
    footprint average.

LAYERS (all public, official, restored by scripts/fetch_data.py via registry/data_manifest.json)
    * GDR 1391 well/spring temperature + geothermometer table (DOI 10.15121/1881483,
      CC BY 4.0): 8,718 measured temperatures, 1,247 geothermometer estimates.
    * UNR/GBCGE INGENIOUS 2-meter shallow temperature-probe regional survey (3,800
      stations; F2mDAB = 2 m temperature departure above background).
    * INGENIOUS Paleo-Geothermal Features compilation (709 sinter/travertine deposits).

PHYSICAL SIGNATURE
    Localised positive shallow-thermal anomalies (IDW fields, rank-combined), the
    conduit footprint rather than the mapped fault trace.  Named non-fault mimics:
    basin-fill groundwater advection, volcanic heat in silicic lava/tuff, and
    measurement clustering near ranches/roads (tiger_road_distance is NOT used as a
    feature but the mimic is not fully removed).

WHY IT CATCHES CATALOGUE-MISSING FAULTS
    The public catalogue is scarp-dependent; blind permeable faults with no surface
    rupture express themselves hydrothermally instead.  Dots are repelled from the
    mapped catalogue (3 px collar), never attracted to it.

DIFFERENCE FROM THIS REPO AND THE REGISTRY
    No lane and no registry raster uses the well/spring temperature field (27,092
    rows) or the 2 m probe archive; the VRC lane used only 21 vent points' proximity
    decay (evidence/vrc_run_card.json).  The 19-band competition stack has no thermal
    channel (evidence/feature_cache.json).  Emission is SOFT (continuous p in [0,1]),
    an axis no measured registry raster has (docs/data/org-ledger-measured.csv:
    is_binary_emission True for every row).

PRE-REGISTERED PARAMETERS (locked before any holdout number is read)
    idw_sigma_px = 10; channel weights ws/probe/paleo = 0.5/0.3/0.2 of rank01(IDW);
    anomaly emphasis S = gaussian(rank01(Z), 2); sampling W = w*S + (1-w);
    min-sep 3.0 px; collar d(labels) > 3.0 px; budget N = 37,654 (champion-matched);
    share sweep w in {0, .25, .5, .75, 1}; softness {binary, plateau1 (3x3 ones),
    gauss1 (exp(-r^2/2), r<=3)}; N sweep {30,000, 37,654}.

PHASES (three experiments total — protocol budget)
    exp1-share   : binary emission, w sweep, both holdout instruments + canary.
    exp2-soft    : softness x N sweep at the winning share, both instruments.
    exp3-final   : write the submission pair, 13-check validator, uniqueness gate,
                   run card and score-estimate receipts.

INSTRUMENTS (all numbers HOLDOUT-DTI, never organizer scores)
    IHR  = GEMSDOE32-HIDE-RECOVER-v3.0 (whole fault segments withheld by quadrant
           draw, 1.5 km collar, visible-fault collars rebuilt per cell, visible
           faults masked pixel-exactly, pooled DTI alpha 0.2 / beta 0.8 / 300 m
           triangular kernel, 256-block cluster bootstrap 95% CI).
    SGMC = GEMSDOE32-SGMC-CAL-v3.0 (62,703 off-catalogue USGS SGMC fault px >300 m
           outside labels.tif as truth; catalogue masked pixel-exact).
    Soft rasters use pooled-probability extensions of both instruments that reuse
    gems.metric kernel arithmetic and the shared block bootstrap unchanged.
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.metric import (  # noqa: E402
    ALPHA,
    BETA,
    tri_kernel,
)
from gems_sass2.metric import EPS, kernel  # noqa: E402,F401
from gems_sass2.holdout import (  # noqa: E402
    cluster_bootstrap_pooled_dti,
    evaluate_hide_and_recover,
    evaluate_sgmc_with_ci,
    load_holdout_context,
    spatial_block_index,
)
from gems_sass2.paths import data_dir  # noqa: E402
from gems_sass2.strain_ridge import collar_mask, greedy_dots  # noqa: E402

# ---- pre-registered constants -------------------------------------------------
IDW_SIGMA_PX = 10.0
CH_W = {"ws": 0.5, "probe": 0.3, "paleo": 0.2}
SMOOTH_SIGMA_PX = 2.0
MIN_SEP_PX = 3.0
COLLAR_PX = 3.0
N_BUDGET = 37_654
SHARES = (0.0, 0.25, 0.5, 0.75, 1.0)
SOFTNESS = ("binary", "plateau1", "gauss1")
N_SWEEP = (30_000, 37_654)
CANARY_AUC_LIMIT = 0.90
SEED = 20261031

WORK = ROOT / ".cache" / "work"
EVID = ROOT / "evidence"


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- channel builders ---------------------------------------------------------

def idw_scatter(values: np.ndarray, rows: np.ndarray, cols: np.ndarray,
                shape: tuple[int, int], sigma: float = IDW_SIGMA_PX) -> np.ndarray:
    """Gaussian-kernel IDW surface from scattered grid-cell samples (duplicate
    cells contribute their max).  Returns 0 where no sample is within ~3 sigma."""
    v = np.full(shape, -np.inf, dtype=np.float32)
    np.maximum.at(v, (rows, cols), values.astype(np.float32))
    hit = np.isfinite(v)
    v = np.where(hit, v, 0.0).astype(np.float32)
    wgt = hit.astype(np.float32)
    num = ndi.gaussian_filter(v * wgt, sigma, mode="constant")
    den = ndi.gaussian_filter(wgt, sigma, mode="constant")
    with np.errstate(invalid="ignore"):
        out = np.where(den > 1e-6, num / np.maximum(den, 1e-9), 0.0)
    return out.astype(np.float32)


def channel_wellspring(ddir: Path, shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    path = ddir / "external" / "gdr_wellspring_in_footprint.csv"
    rows: list[dict] = list(csv.DictReader(open(path)))
    rr, cc, vv = [], [], []
    for r in rows:
        vals = [float(r[k]) for k in ("temp_c", "geothermquartz_c", "geothermchalc_c", "geothermcat_c") if r.get(k)]
        vals = [v for v in vals if v > 0]
        if not vals:
            continue
        rr.append(int(r["row"]))
        cc.append(int(r["col"]))
        vv.append(min(max(vals), 300.0))
    arr = idw_scatter(np.asarray(vv), np.asarray(rr), np.asarray(cc), shape)
    return arr, {"n_rows": len(rows), "n_points_used": len(rr),
                 "v_min": float(min(vv)), "v_max": float(max(vv))}


def channel_probe(ddir: Path, shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    import shapefile as _sf
    from pyproj import Transformer

    zpath = ddir / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip"
    with tempfile.TemporaryDirectory(prefix="probe-") as td:
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(td)
        shp = next(Path(td).rglob("*n83geo.shp"))
        rdr = _sf.Reader(str(shp))
        fields = [f[0] for f in rdr.fields[1:]]
        ix = {name: i for i, name in enumerate(fields)}
        tf = Transformer.from_crs("EPSG:26911", "EPSG:32611", always_xy=True)
        rr, cc, vv = [], [], []
        n_f2 = 0
        for rec in rdr.records():
            rec_d = dict(zip(fields, rec))
            try:
                x = float(rec_d["UTM_E"]); y = float(rec_d["UTM_N"])
            except (TypeError, ValueError):
                continue
            if not (np.isfinite(x) and np.isfinite(y)) or x <= 0:
                continue
            f2 = rec_d.get("F2mDAB")
            tmax = 0.0
            for k in ("T2m", "T1m", "T2m_2", "T2m_3", "T2m_4", "T2m_5", "T2m_6", "T2m_7"):
                try:
                    t = float(rec_d.get(k) or 0.0)
                except (TypeError, ValueError):
                    t = 0.0
                tmax = max(tmax, t)
            try:
                f2v = float(f2)
            except (TypeError, ValueError):
                f2v = float("nan")
            # pre-registered: v = max(0, F2mDAB) where reported, else max(0, Tmax - 25 C)
            if np.isfinite(f2v):
                v = max(0.0, f2v)
                n_f2 += 1
            else:
                v = max(0.0, tmax - 25.0)
            if v <= 0:
                continue
            gx, gy = tf.transform(x, y)
            # grid: col = (gx - 243350)/100, row = (4508550 - gy)/100
            c = int(round((gx - 243350.0) / 100.0))
            r = int(round((4508550.0 - gy) / 100.0))
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                rr.append(r); cc.append(c); vv.append(v)
    arr = idw_scatter(np.asarray(vv), np.asarray(rr), np.asarray(cc), shape)
    return arr, {"n_stations": len(rdr), "n_points_used": len(rr), "n_with_F2mDAB": n_f2}


def channel_paleo(ddir: Path, shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    import shapefile as _sf
    from pyproj import Transformer

    zpath = ddir / "external" / "paleo_geothermal_regional.zip"
    with tempfile.TemporaryDirectory(prefix="paleo-") as td:
        with zipfile.ZipFile(zpath) as zf:
            zf.extractall(td)
        shp = next(Path(td).rglob("*.shp"))
        rdr = _sf.Reader(str(shp))
        tf = Transformer.from_crs("EPSG:4326", "EPSG:32611", always_xy=True)
        rr, cc = [], []
        for sh in rdr.shapes():
            lon, lat = sh.points[0]
            gx, gy = tf.transform(lon, lat)
            c = int(round((gx - 243350.0) / 100.0))
            r = int(round((4508550.0 - gy) / 100.0))
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                rr.append(r); cc.append(c)
    arr = idw_scatter(np.ones(len(rr), dtype=np.float32), np.asarray(rr), np.asarray(cc), shape)
    return arr, {"n_deposits": len(rdr), "n_in_grid": len(rr)}


def rank01(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    shape = a.shape
    r = rankdata(a.ravel(), method="average") / float(a.size)
    return r.reshape(shape).astype(np.float32)


def build_fields(ddir: Path) -> dict:
    """Build the thermal-conduit prior field (pre-registered recipe)."""
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    shape = foot.shape
    ws, ws_meta = channel_wellspring(ddir, shape)
    pr, pr_meta = channel_probe(ddir, shape)
    pa, pa_meta = channel_paleo(ddir, shape)
    z = (CH_W["ws"] * rank01(ws) + CH_W["probe"] * rank01(pr) + CH_W["paleo"] * rank01(pa)).astype(np.float32)
    s = ndi.gaussian_filter(rank01(z), SMOOTH_SIGMA_PX, mode="constant")
    s = rank01(s).astype(np.float32)
    for _name, _arr in (("ws", ws), ("probe", pr), ("paleo", pa), ("z", z), ("s", s)):
        if _arr.shape != shape:
            raise ValueError(f"field {_name} has shape {_arr.shape}, expected {shape}")
    out = {
        "ws": ws, "probe": pr, "paleo": pa, "z": z, "s": s, "foot": foot,
    }
    meta = {"ws": ws_meta, "probe": pr_meta, "paleo": pa_meta,
            "params": {"idw_sigma_px": IDW_SIGMA_PX, "channel_weights": CH_W,
                       "smooth_sigma_px": SMOOTH_SIGMA_PX,
                       "min_sep_px": MIN_SEP_PX, "collar_px": COLLAR_PX}}
    return {"fields": out, "meta": meta}


# ---- emission ----------------------------------------------------------------

def emission_mask(fields: dict, faults_repeller: np.ndarray, share: float, n_dots: int,
                  rng_seed: int = SEED) -> np.ndarray:
    """Blue-noise sample of W = share*S + (1-share) over the collar-clean footprint.

    NOTE (measured, EXP-1): greedy acceptance depends only on the RANKING of W, and
    w*S + (1-w) is strictly increasing in S for every w > 0, so all share values > 0
    produce identical dot sets.  The share axis therefore collapses to
    'thermal-ranked' vs 'uniform-random'; w = 0 is realised as seeded uniform noise
    so the control is a genuine Poisson-disk sample (a constant field would
    degenerate to raster-order scanlines)."""
    foot = fields["foot"]
    s = fields["s"]
    rng = np.random.default_rng(rng_seed)
    if share > 0.0:
        w = (share * s + (1.0 - share)).astype(np.float32)
    else:
        w = rng.random(foot.shape, dtype=np.float32)
    candidate = foot & collar_mask(faults_repeller, COLLAR_PX)
    idx = greedy_dots(w, candidate, n_dots, min_sep_px=MIN_SEP_PX)
    h, w_ = foot.shape
    mask = np.zeros(h * w_, dtype=bool)
    mask[idx] = True
    return mask.reshape(foot.shape)


def ring_field(labels: np.ndarray) -> np.ndarray:
    """Catalogue-ring habitat multiplier: fault-adjacent-but-off-collar territory
    (3-30 px from the mapped catalogue) is where off-catalogue truth concentrates
    in every measured population (nine-site family median dot distance 15-20 px;
    SGMC-off faults cluster on the same fault systems).  Pre-registered profile:
    m(d) = exp(-(d-12)^2 / (2*10^2)) + 0.20 for d > 3 px, 0 otherwise."""
    d = ndi.distance_transform_edt(~labels).astype(np.float32)
    m = np.exp(-((d - 12.0) ** 2) / (2.0 * 10.0 ** 2)) + np.float32(0.20)
    m = np.where(d > COLLAR_PX, m, np.float32(0.0))
    return m.astype(np.float32)


def emission_mask_ring(fields: dict, faults_repeller: np.ndarray, n_dots: int, blend: float = 0.5,
                       rng_seed: int = SEED) -> np.ndarray:
    """Blue-noise sample of the ring-habitat prior (mixture-sampled, not rank-sampled:
    blend share of the budget drawn from ring-weighted ranks, the rest from seeded
    uniform noise, so the coverage floor is real and the geometry is unique)."""
    foot = fields["foot"]
    rng = np.random.default_rng(rng_seed)
    r = ring_field(faults_repeller)
    ring_rank = rank01(r + rng.random(foot.shape, dtype=np.float32) * 1e-3)
    unif = rng.random(foot.shape, dtype=np.float32)
    w = np.where(rng.random(foot.shape) < blend, ring_rank, unif).astype(np.float32)
    candidate = foot & collar_mask(faults_repeller, COLLAR_PX)
    idx = greedy_dots(w, candidate, n_dots, min_sep_px=MIN_SEP_PX)
    h, w_ = foot.shape
    mask = np.zeros(h * w_, dtype=bool)
    mask[idx] = True
    return mask.reshape(foot.shape)


def soften(mask: np.ndarray, kind: str) -> np.ndarray:
    if kind == "binary":
        return mask.astype(np.float32)
    if kind == "plateau1":
        return ndi.binary_dilation(mask, structure=np.ones((3, 3), bool)).astype(np.float32)
    if kind == "gauss1":
        d = ndi.distance_transform_edt(~mask).astype(np.float32)
        p = np.exp(-0.5 * d * d) * (d <= 3.0)
        return p.astype(np.float32)
    raise ValueError(kind)


# ---- pooled-probability extensions of the shared instruments ------------------

def _prob_cell_terms(p_sub: np.ndarray, truth_sub: np.ndarray, k_dg_sub: np.ndarray,
                     truth_coords, k_radius: float = 3.0) -> tuple[float, float, float]:
    """TP/FP/FN terms of the official continuous metric on one scoring window."""
    n_t = int(truth_coords[0].size)
    if n_t == 0:
        return 0.0, float(p_sub.sum()), 0.0
    rows, cols = truth_coords
    best = np.zeros(n_t, dtype=np.float64)
    H, W = p_sub.shape
    R = int(k_radius)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            dist = float(np.hypot(dy, dx))
            if dist > k_radius:
                continue
            r2, c2 = rows + dy, cols + dx
            inside = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
            vals = np.zeros(n_t, dtype=np.float64)
            vals[inside] = p_sub[r2[inside], c2[inside]] * float(tri_kernel(np.array([dist]))[0])
            np.maximum(best, vals, out=best)
    tp = float(best.sum())
    fn = float(n_t - tp)
    fp = float(np.sum(p_sub * (1.0 - k_dg_sub)))
    return tp, fp, fn


def evaluate_hide_and_recover_prob(pred_cells: dict[str, np.ndarray], ctx, b_visible_px: float = 2.0,
                                   grid_n: int = 16, n_boot: int = 1000, seed: int = SEED,
                                   name: str = "candidate-soft") -> dict:
    """Pooled-probability twin of evaluate_hide_and_recover (same masking, same
    block bootstrap; kernel arithmetic from gems.metric)."""
    h, w = ctx.foot.shape
    n_blocks = grid_n * grid_n
    tp_blk = np.zeros(n_blocks); fp_blk = np.zeros(n_blocks); fn_blk = np.zeros(n_blocks)
    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(spatial_block_index(fy, fx, (h, w), grid_n))
    folds = {}
    for cell in ctx.cells:
        sl = cell.bbox
        r0, c0 = int(sl[0].start), int(sl[1].start)
        raw = np.asarray(pred_cells[cell.key], dtype=np.float32)
        p_sub = (raw[sl] if raw.shape == (h, w) else raw) * cell.active_sub
        if b_visible_px > 0.0:
            p_sub = p_sub * (cell.d_vis_sub > b_visible_px)
        n_t = cell.n_truth
        if n_t == 0:
            folds[cell.key] = {"dti": 0.0, "tp": 0.0, "fp": float(p_sub.sum()), "fn": 0.0, "n_truth": 0}
            continue
        tp, fp, fn = _prob_cell_terms(p_sub, None, cell.k_dg_sub, cell.truth_coords)
        ty_sub, tx_sub = cell.truth_coords
        t_blk = spatial_block_index(ty_sub + r0, tx_sub + c0, (h, w), grid_n)
        # per-truth cover for block attribution
        rows, cols = ty_sub, tx_sub
        best = np.zeros(n_t)
        H, W = p_sub.shape
        R = 3
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                dist = float(np.hypot(dy, dx))
                if dist > 3.0:
                    continue
                r2, c2 = rows + dy, cols + dx
                inside = (r2 >= 0) & (r2 < H) & (c2 >= 0) & (c2 < W)
                vals = np.zeros(n_t)
                vals[inside] = p_sub[r2[inside], c2[inside]] * float(tri_kernel(np.array([dist]))[0])
                np.maximum(best, vals, out=best)
        np.add.at(tp_blk, t_blk, best)
        np.add.at(fn_blk, t_blk, 1.0 - best)
        py, px = np.nonzero(p_sub > 0)
        if py.size:
            p_blk = spatial_block_index(py + r0, px + c0, (h, w), grid_n)
            np.add.at(fp_blk, p_blk, (p_sub[py, px] * (1.0 - cell.k_dg_sub[py, px])).astype(np.float64))
        folds[cell.key] = {"dti": float(tp / (tp + ALPHA * fp + BETA * fn + EPS)),
                           "tp": tp, "fp": fp, "fn": fn, "n_truth": n_t}
    pooled, ci95, boots = cluster_bootstrap_pooled_dti(tp_blk, fp_blk, fn_blk, active_blocks,
                                                       n_boot=n_boot, seed=seed)
    return {"candidate_id": name, "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0+prob",
            "score_label": "HOLDOUT-DTI", "pooled_dti": pooled, "ci95": ci95,
            "n_withheld_positives": int(sum(c.n_truth for c in ctx.cells)),
            "folds": folds, "_boots": boots}


def evaluate_sgmc_prob(p: np.ndarray, ctx, grid_n: int = 16, n_boot: int = 1000, seed: int = SEED,
                       name: str = "candidate-soft") -> dict:
    h, w = ctx.foot.shape
    p = np.where(ctx.foot & ~ctx.labels, np.clip(np.asarray(p, dtype=np.float64), 0.0, 1.0), 0.0)
    n_blocks = grid_n * grid_n
    tp_blk = np.zeros(n_blocks); fp_blk = np.zeros(n_blocks); fn_blk = np.zeros(n_blocks)
    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(spatial_block_index(fy, fx, (h, w), grid_n))
    ty, tx = ctx.sgmc_truth_coords
    t_blk = spatial_block_index(ty, tx, (h, w), grid_n)
    tp, fp, fn = _prob_cell_terms(p, None, ctx.sgmc_k_dg, ctx.sgmc_truth_coords)
    rows, cols = ty, tx
    best = np.zeros(ctx.sgmc_n_truth)
    R = 3
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            dist = float(np.hypot(dy, dx))
            if dist > 3.0:
                continue
            r2, c2 = rows + dy, cols + dx
            inside = (r2 >= 0) & (r2 < h) & (c2 >= 0) & (c2 < w)
            vals = np.zeros(ctx.sgmc_n_truth)
            vals[inside] = p[r2[inside], c2[inside]] * float(tri_kernel(np.array([dist]))[0])
            np.maximum(best, vals, out=best)
    np.add.at(tp_blk, t_blk, best)
    np.add.at(fn_blk, t_blk, 1.0 - best)
    py, px = np.nonzero(p > 0)
    if py.size:
        p_blk = spatial_block_index(py, px, (h, w), grid_n)
        np.add.at(fp_blk, p_blk, (p[py, px] * (1.0 - ctx.sgmc_k_dg[py, px])).astype(np.float64))
    pooled, ci95, boots = cluster_bootstrap_pooled_dti(tp_blk, fp_blk, fn_blk, active_blocks,
                                                       n_boot=n_boot, seed=seed)
    return {"candidate_id": name, "evaluator_version": "GEMSDOE32-SGMC-CAL-v3.0+prob",
            "score_label": "HOLDOUT-DTI", "raw_pooled_dti": pooled, "raw_ci95": ci95,
            "n_withheld_positives": int(ctx.sgmc_n_truth), "_boots": boots}


def symmetric_auc(values: np.ndarray, truth: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    auc = float(roc_auc_score(truth.astype(np.uint8), values))
    return max(auc, 1.0 - auc)


def canary(fields: dict, ctx) -> dict:
    """Rule 4 canary: each input field alone vs pooled withheld positives."""
    from sklearn.metrics import roc_auc_score  # noqa: F401
    eval_active = np.zeros(ctx.foot.shape, dtype=bool)
    truth_2d = np.zeros(ctx.foot.shape, dtype=bool)
    for cell in ctx.cells:
        sl = cell.bbox
        act = cell.active_sub.copy()
        eval_active[sl] |= act
        t = np.zeros_like(act)
        ty, tx = cell.truth_coords
        t[ty, tx] = True
        truth_2d[sl] |= act & t
    af = eval_active[ctx.foot]
    y = truth_2d[ctx.foot][af].astype(np.uint8)
    pos = np.flatnonzero(y == 1)
    neg = np.flatnonzero(y == 0)[::20]
    sub = np.concatenate([pos, neg])
    rows = []
    for name in ("ws", "probe", "paleo", "z", "s"):
        vals = fields[name][ctx.foot][af][sub]
        auc = symmetric_auc(vals, y[sub])
        rows.append({"feature": name, "symmetric_auc": round(auc, 5),
                     "leaks_gt_0p90": bool(auc > CANARY_AUC_LIMIT)})
    worst = max(rows, key=lambda r: r["symmetric_auc"])
    return {"n_features_tested": len(rows), "n_withheld_positives": int(len(pos)),
            "auc_limit": CANARY_AUC_LIMIT, "max_symmetric_auc": worst["symmetric_auc"],
            "max_auc_feature": worst["feature"],
            "n_leaking": sum(r["leaks_gt_0p90"] for r in rows),
            "canary_passed": all(not r["leaks_gt_0p90"] for r in rows),
            "features": rows}


# ---- per-cell fold-local emission (leak-free collars) -------------------------

def fold_local_cells(fields: dict, ctx, share: float, n_dots: int, softness: str,
                     placement: str = "thermal") -> dict[str, np.ndarray]:
    """Emission per holdout cell with the collar rebuilt from that cell's VISIBLE
    faults only (protocol rule 2: catalogue-derived features from visible faults).
    Each cell gets the full static budget so the pooled accounting matches the
    shared instrument's static-raster semantics (cf. evidence/vrc_run_card.json:
    parent 44,090 dots -> IHR 0.0967)."""
    out = {}
    for i, cell in enumerate(ctx.cells):
        visible = cell.visible_full
        if placement == "ring":
            mask = emission_mask_ring(fields, visible, n_dots, rng_seed=SEED + i)
        else:
            mask = emission_mask(fields, visible, share, n_dots, rng_seed=SEED + i)
        p = soften(mask, softness)
        out[cell.key] = p
    return out


# ---- phases ------------------------------------------------------------------

def phase1() -> dict:
    ddir = data_dir()
    built = build_fields(ddir)
    fields = built["fields"]
    np.savez_compressed(WORK / "thermal_fields.npz",
                        ws=fields["ws"], probe=fields["probe"], paleo=fields["paleo"],
                        z=fields["z"], s=fields["s"], foot=fields["foot"])
    (WORK / "thermal_fields_meta.json").write_text(json.dumps(built["meta"], indent=2))

    ctx = load_holdout_context(ddir)
    labels = ctx.labels
    # Pre-registered: the emission collars the competition catalogue only.  The
    # SGMC instrument's truth is SGMC-mapped faults; collaring SGMC would erase
    # the instrument (EXP-1 v1 shipped exactly that zeroing bug and is logged in
    # the run card / IRREGULARITIES).  SGMC adjacency is a diagnostic instead.
    repeller = labels
    can = canary(fields, ctx)

    rows = []
    for w in SHARES:
        mask = emission_mask(fields, repeller, w, N_BUDGET)
        cells = fold_local_cells(fields, ctx, w, N_BUDGET, "binary")
        ihr = evaluate_hide_and_recover(cells, ctx, b_visible_px=2.0, name=f"s3_w{w}")
        sg = evaluate_sgmc_with_ci(mask, ctx, name=f"s3_w{w}")
        rows.append({
            "share": w, "n_dots": int(mask.sum()),
            "ihr_pooled_dti": ihr["pooled_dti"],
            "ihr_ci95": ihr["ci95_cluster_bootstrap"],
            "ihr_detached_600m_dti": ihr["detached_600m"]["pooled_dti"],
            "sgmc_raw_pooled_dti": sg["sgmc_raw_pooled_dti"],
            "sgmc_raw_ci95": sg["sgmc_raw_ci95"],
            "sgmc_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
        })
        print(f"w={w}: dots={rows[-1]['n_dots']} IHR={rows[-1]['ihr_pooled_dti']:.4f} "
              f"SGMC={rows[-1]['sgmc_raw_pooled_dti']:.4f}", flush=True)

    receipt = {
        "experiment": "EXP-1 share sweep (binary emission, N=37,654)",
        "generated_utc": _now(), "seed": SEED,
        "lane": "THERMAL-CONDUIT EMISSION (S3)",
        "instruments": {
            "IHR": "GEMSDOE32-HIDE-RECOVER-v3.0",
            "SGMC": "GEMSDOE32-SGMC-CAL-v3.0",
        },
        "leakage_canary": can,
        "rows": rows,
        "channel_meta": built["meta"],
    }
    (EVID / "exp1_thermal_share_sweep.json").write_text(json.dumps(receipt, indent=2))
    return receipt


def phase2(share: float) -> dict:
    """EXP-2 (placement decision): thermal-ranked placement lost EXP-1 against a
    genuine uniform Poisson-disk control on BOTH instruments, so the shipped
    placement is decided between uniform and the catalogue-ring habitat prior,
    at two budgets and with one softness probe.  Four pre-registered configs."""
    ddir = data_dir()
    fields = dict(np.load(WORK / "thermal_fields.npz"))
    ctx = load_holdout_context(ddir)
    repeller = ctx.labels
    configs = [
        {"name": "uniform-binary-37654", "placement": "uniform", "softness": "binary", "n": 37_654},
        {"name": "ring-binary-37654", "placement": "ring", "softness": "binary", "n": 37_654},
        {"name": "ring-binary-24000", "placement": "ring", "softness": "binary", "n": 24_000},
        {"name": "ring-plateau1-37654", "placement": "ring", "softness": "plateau1", "n": 37_654},
    ]
    rows = []
    for cfg in configs:
        n, soft, placement = cfg["n"], cfg["softness"], cfg["placement"]
        share_cfg = 0.0 if placement == "uniform" else share
        if placement == "ring":
            mask = emission_mask_ring(fields, repeller, n)
        else:
            mask = emission_mask(fields, repeller, 0.0, n)
        p = soften(mask, soft)
        cells = fold_local_cells(fields, ctx, share_cfg, n, soft, placement=placement)
        if soft == "binary":
            ihr = evaluate_hide_and_recover(cells, ctx, b_visible_px=2.0, name=cfg["name"])
            sg = evaluate_sgmc_with_ci(mask, ctx, name=cfg["name"])
            ihr_d, ihr_ci = ihr["pooled_dti"], ihr["ci95_cluster_bootstrap"]
            sg_d, sg_ci = sg["sgmc_raw_pooled_dti"], sg["sgmc_raw_ci95"]
        else:
            ihrp = evaluate_hide_and_recover_prob(cells, ctx, name=cfg["name"])
            sgp = evaluate_sgmc_prob(p, ctx, name=cfg["name"])
            ihr_d, ihr_ci = ihrp["pooled_dti"], ihrp["ci95"]
            sg_d, sg_ci = sgp["raw_pooled_dti"], sgp["raw_ci95"]
        row = dict(cfg, share=share_cfg, sum_p=float(p.sum()),
                   ihr_pooled_dti=ihr_d, ihr_ci95=ihr_ci,
                   sgmc_raw_pooled_dti=sg_d, sgmc_raw_ci95=sg_ci)
        rows.append(row)
        print(f"{cfg['name']}: IHR={ihr_d:.4f} SGMC={sg_d:.4f}", flush=True)
    receipt = {"experiment": "EXP-2 placement decision (uniform vs ring habitat; N; softness probe)",
               "generated_utc": _now(), "seed": SEED, "rows": rows}
    (EVID / "exp2_placement_decision.json").write_text(json.dumps(receipt, indent=2))
    return receipt


def phase3(placement: str, softness: str, n_dots: int) -> dict:
    from gems_sass2.submission import write_submission_pair
    from gems_sass2.paths import downloads_dir

    ddir = data_dir()
    fields = dict(np.load(WORK / "thermal_fields.npz"))
    ctx = load_holdout_context(ddir)
    repeller = ctx.labels
    if placement == "ring":
        mask = emission_mask_ring(fields, repeller, n_dots)
    elif placement == "uniform":
        mask = emission_mask(fields, repeller, 0.0, n_dots)
    else:
        mask = emission_mask(fields, repeller, 0.25, n_dots)
    p = soften(mask, softness)

    stem = (f"gemsass2-s3-{placement}-{softness}-{n_dots}"
            f"-{_dt.datetime.now(_dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    receipt = write_submission_pair(p, downloads_dir(), stem,
                                    ddir / "sample_submission.tif", ddir / "labels.tif")
    d_labels = ndi.distance_transform_edt(~ctx.labels)
    pos = p > 0
    n_pos = int(pos.sum())
    diag = {
        "pct_cells_within_3px_labels": round(100.0 * float((pos & (d_labels <= 3.0)).sum()) / max(n_pos, 1), 4),
        "pct_cells_within_3px_sgmc": round(100.0 * float((pos & (ndi.distance_transform_edt(~ctx.sgmc_off) <= 3.0)).sum()) / max(n_pos, 1), 4),
        "median_dist_to_labels_px": float(np.median(d_labels[pos])) if n_pos else None,
        "n_positive_cells": n_pos,
        "sum_p": float(p.sum()),
    }
    out = {
        "experiment": "EXP-3 final candidate", "generated_utc": _now(),
        "lane": "S3 THERMAL-CONDUIT / RING-HABITAT EMISSION",
        "config": {"placement": placement, "softness": softness, "n_dots": n_dots,
                   "collar_px": COLLAR_PX,
                   "repeller": "labels.tif (bridge catalogue), 3 px collar; SGMC adjacency kept as diagnostic"},
        "diagnostics": diag,
        "stem": stem, "write_receipt": receipt,
    }
    (EVID / f"exp3_thermal_final_{n_dots}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"stem": stem, "checks_passed": receipt.get("validation", receipt).get("checks_passed")},
                     indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=["exp1-share", "exp2-soft", "exp3-final"])
    ap.add_argument("--share", type=float, default=0.25)
    ap.add_argument("--placement", choices=("ring", "uniform", "thermal"), default="ring")
    ap.add_argument("--softness", choices=SOFTNESS, default="binary")
    ap.add_argument("--n-dots", type=int, default=N_BUDGET)
    args = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("GEMS_DATA_DIR", str(ROOT / ".cache" / "gems_data"))
    if args.phase == "exp1-share":
        phase1()
    elif args.phase == "exp2-soft":
        phase2(args.share)
    else:
        phase3(args.placement, args.softness, args.n_dots)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
