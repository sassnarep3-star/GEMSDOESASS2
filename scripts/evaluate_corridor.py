#!/usr/bin/env python3
"""Evaluate the H-CORRIDOR emission against the champion lineage, controlling the
one thing the official metric charges for: total emitted probability mass.

Under the official metric
    DTI = TP_w / (0.2*TP_w + 0.2*FP_w + 0.8*|G|),  FP_w = sum_x p(x)[1 - max_g k]
the false-positive bill is driven by SUM_x p(x), not by the number of nonzero
pixels.  So every candidate below is emitted at exactly the champion's mass
(sum p = 37,654) and compared like for like.

Three deliverables:
  1. leakage canary  - spatially blocked out-of-fold AUC of the probability model
  2. enrichment      - is the champion's dot set geophysically informed at all?
  3. mass-matched    - proxy DTI of corridor emissions vs the champion raster
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, maximum_filter
from sklearn.metrics import roc_auc_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems.metric import dti_binary, dti_probabilistic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
REG = ROOT / ".cache/registry"
CHAMP_MASS = 37654.0


def block_folds(H, W, nb=4):
    yy, xx = np.mgrid[0:H, 0:W]
    by = (yy * nb // H)
    bx = (xx * nb // W)
    lab = by * nb + bx
    return lab


def main() -> int:
    meta = json.loads((WORK / "cube_meta.json").read_text())
    names = meta["band_names"]
    H, W = meta["grid"]["shape"]
    footprint = np.load(WORK / "footprint.npy")
    labels = np.load(WORK / "qfaults_labels.npy")
    prob = np.lib.format.open_memmap(WORK / "cand_prob.f32", mode="r", dtype=np.float32, shape=(H, W))
    with rasterio.open(ROOT / ".cache/mirror/GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    near2 = binary_dilation(labels, np.ones((5, 5), bool))
    truths = {
        "P_SGMC2": sgmc & ~near2 & footprint,
        "P_SGMC0": sgmc & footprint,
        "P_LABELS": labels & footprint,
    }

    report: dict = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "note": "PROXY-HOLDOUT-DTI on measurable proxy truth sets. Reported leaderboard "
                "scores are OWNER-REPORTED. No organizer receipt exists for any file here.",
    }

    # ---------------- 2. enrichment: is the champion geophysically informed? ------------
    champ_path = REG / "GEMSDOE32.tif"
    with rasterio.open(champ_path) as ds:
        champ = ds.read(1).astype(np.float64)
    champ[~np.isfinite(champ)] = 0.0
    champ_mask = champ > 0
    rng = np.random.default_rng(7)
    fp_idx = np.flatnonzero(footprint.ravel())
    rand_idx = rng.choice(fp_idx, 2_000_000, replace=False)
    p_rand = np.asarray(prob).ravel()[rand_idx]
    p_champ = np.asarray(prob).ravel()[np.flatnonzero(champ_mask.ravel())]
    q = lambda a, v: float(np.percentile(a, v))
    report["enrichment"] = {
        "question": "Are the champion's dots at higher model probability than random footprint cells?",
        "champion_dots": int(champ_mask.sum()),
        "median_prob_champion": round(float(np.median(p_champ)), 5),
        "median_prob_random": round(float(np.median(p_rand)), 5),
        "mean_prob_champion": round(float(p_champ.mean()), 5),
        "mean_prob_random": round(float(p_rand.mean()), 5),
        "p90_champion": round(q(p_champ, 90), 5),
        "p90_random": round(q(p_rand, 90), 5),
        "ratio_of_means": round(float(p_champ.mean() / p_rand.mean()), 4),
        "auc_model_vs_known_faults_footprint": round(float(roc_auc_score(
            labels.ravel()[rand_idx], p_rand)), 4),
    }

    # ---------------- 1. leakage canary: spatially blocked OOF AUC ---------------------
    lab = block_folds(H, W, nb=4)
    # 4 folds, each = one diagonal class of the 4x4 block grid -> spatially separated
    fold = (np.arange(H)[:, None] * 4 // H + np.arange(W)[None, :] * 4 // W) % 4
    fold = np.broadcast_to(fold, (H, W)).copy()
    keep = [i for i, n in enumerate(names) if not n.startswith(("qfv:", "sgm:"))]
    cube = np.lib.format.open_memmap(WORK / "cube.f32", mode="r", dtype=np.float32, shape=(len(names), H, W))
    deriv = np.lib.format.open_memmap(WORK / "deriv.f32", mode="r", dtype=np.float32,
                                      shape=(2 * 6, H, W))
    nfeat = len(keep) + deriv.shape[0]
    rows, cols = np.nonzero(footprint)
    y_all = labels[rows, cols].astype(np.uint8)
    sel = rng.choice(rows.size, size=1_200_000, replace=False)
    rows_s, cols_s, y_s = rows[sel], cols[sel], y_all[sel]
    fold_s = fold[rows_s, cols_s]
    X = np.empty((rows_s.size, nfeat), np.float32)
    for r0 in range(0, H, 250):
        r1 = min(r0 + 250, H)
        m = (rows_s >= r0) & (rows_s < r1)
        if not m.any():
            continue
        blk = np.empty((len(keep), r1 - r0, W), np.float32)
        for k, i in enumerate(keep):
            blk[k] = cube[i, r0:r1, :]
        d = np.asarray(deriv[:, r0:r1, :], np.float32)
        X[m, :len(keep)] = blk[:, rows_s[m] - r0, cols_s[m]].T
        X[m, len(keep):] = d[:, rows_s[m] - r0, cols_s[m]].T
        del blk, d
    from sklearn.ensemble import HistGradientBoostingClassifier
    oof = np.empty(y_s.size, np.float32)
    folds = sorted(set(fold_s.tolist()))
    for f in folds:
        tr = fold_s != f
        te = fold_s == f
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06,
                                             max_leaf_nodes=31, l2_regularization=1.0,
                                             random_state=7)
        clf.fit(X[tr], y_s[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    report["leakage_canary"] = {
        "design": "4 spatially disjoint fold classes (4x4 block grid taken modulo 4); model "
                  "trained on 1.2 M sampled footprint cells, never on the held-out blocks.",
        "spatially_blocked_oof_auc": round(float(roc_auc_score(y_s, oof)), 4),
        "alarm_threshold": 0.90,
        "verdict": "PASS (below 0.90)" if roc_auc_score(y_s, oof) < 0.90 else "ALARM",
        "note": "AUC measures detection of KNOWN catalogue faults, not of the hidden test faults.",
    }
    del X

    # ---------------- 3. mass-matched emissions ----------------------------------------
    p = np.asarray(prob).astype(np.float64)
    p[~footprint] = 0.0
    results = []

    def record(name, emit, extra=None):
        row = {"emission": name, "sum_p": round(float(emit[footprint].sum()), 1),
               "nonzero_px": int((emit[footprint] > 0).sum())}
        for tn, T in truths.items():
            row[tn] = round(float(dti_probabilistic(np.clip(emit, 0, 1), T, footprint)["dti"]), 6)
        if extra:
            row.update(extra)
        results.append(row)
        print(json.dumps(row), flush=True)

    # champion (binary, its own mass)
    record("CHAMPION_GEMSDOE32_binary", np.clip(champ, 0, 1))

    # E1 binary dots, mass-matched, min separation s, off-catalogue collar
    for collar in (0, 2):
        allowed = footprint.copy()
        if collar:
            allowed &= ~binary_dilation(labels, np.ones((2 * collar + 1, 2 * collar + 1), bool))
        for sep in (0, 3, 6, 10):
            score = p.copy()
            score[~allowed] = -1.0
            flat = score.ravel()
            order = np.argsort(-flat)
            emit = np.zeros((H, W), np.float64)
            taken = np.zeros((H, W), bool)
            n = 0
            peak = maximum_filter(p, size=2 * sep + 1) if sep else p
            cand = np.flatnonzero((allowed.ravel()) & ((p >= peak - 1e-12).ravel()))
            cand = cand[np.argsort(-p.ravel()[cand])]
            for idx in cand:
                if n >= int(CHAMP_MASS):
                    break
                r, c = divmod(int(idx), W)
                if taken[r, c]:
                    continue
                emit[r, c] = 1.0
                r0, r1 = max(0, r - sep), min(H, r + sep + 1)
                c0, c1 = max(0, c - sep), min(W, c + sep + 1)
                taken[r0:r1, c0:c1] = True
                n += 1
            record(f"E1_dots_sep{sep}_collar{collar}", emit,
                   {"dots": int(emit.sum()), "catalogue_collar_px": collar})

    # E2 graded corridor: p scaled so total mass == champion mass
    for lo_q in (99.0, 98.0, 95.0, 90.0, 80.0):
        thr = float(np.percentile(p[footprint], lo_q))
        e = np.where(p >= thr, p, 0.0)
        if e.sum() <= 0:
            continue
        record(f"E2_graded_raw_q{lo_q}", np.clip(e, 0, 1),
               {"threshold_p": round(thr, 5)})

    # E3 mass-matched graded corridor: bisect the scale so sum p == champion mass exactly
    def mass_match(mask):
        vals = p[mask]
        if vals.sum() <= 0:
            return np.zeros((H, W), np.float64), 0.0, 0.0
        lo, hi = 0.0, 1.0
        while float(np.clip(vals * hi, 0, 1).sum()) < CHAMP_MASS:
            hi *= 2.0
            if hi > 1e9:
                break
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if float(np.clip(vals * mid, 0, 1).sum()) < CHAMP_MASS:
                lo = mid
            else:
                hi = mid
        scale = 0.5 * (lo + hi)
        e = np.zeros((H, W), np.float64)
        e[mask] = np.clip(vals * scale, 0.0, 1.0)
        return e, scale, float(e.sum())

    for lo_q in (99.9, 99.5, 99.0, 98.0, 95.0, 90.0, 80.0):
        thr = float(np.percentile(p[footprint], lo_q))
        mask = (p >= thr) & footprint
        if not mask.any():
            continue
        e, scale, tot = mass_match(mask)
        record(f"E3_massmatched_q{lo_q}", e,
               {"threshold_p": round(thr, 5), "scale": round(float(scale), 5),
                "support_px": int(mask.sum()), "sum_p_achieved": round(tot, 1)})

    report["emissions"] = results
    out = ROOT / "evidence/corridor_evaluation.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
