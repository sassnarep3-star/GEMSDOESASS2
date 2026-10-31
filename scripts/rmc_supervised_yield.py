#!/usr/bin/env python3
"""Decisive yield test: does a supervised, catalogue-free propensity field beat the
dot-lattice family's *off-catalogue yield* at the same dot budget?

Measured quantity, per emission: credit per emitted pixel against the off-catalogue USGS
SGMC truth (62,703 px that lie >300 m outside `labels.tif`), i.e.

    yield = TP_w / N_emitted

A random placement over the footprint scores yield ~= 0.114 with this truth set (computed
below, no assumption).  The nine-site family's champion scores 0.149.  Anything that wants
to beat the family has to beat 0.149 at comparable budget, because the leaderboard behaves
as DTI ~= 5 * yield in the sparse-truth regime (derivation in knowledge/10).

Model: HistGBT on the 7 RMC channels, trained leave-one-quadrant-out (a quadrant is only
ever predicted by a model that never saw any label inside it, dilated by 80 px), so the
SGMC instrument is untouched by training.

Every number here is HOLDOUT-DTI or a yield measurement.  Nothing is a score.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

import numpy as np
from scipy import ndimage as ndi
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.holdout import (  # noqa: E402
    FOLDS, load_holdout_context, quadrant_ids, evaluate_hide_and_recover, evaluate_sgmc_with_ci,
)
from gems_sass2.metric import ALPHA, BETA, EPS, kernel  # noqa: E402
from gems_sass2.paths import data_dir  # noqa: E402

CACHE = ROOT / ".cache" / "rmc"
CHANNELS = ("S1_pf_lineament", "S2_scarp", "S3_strain", "S4_seismicity",
            "S5_conduit", "S6_basement", "A_geothermal")


def yield_of(mask: np.ndarray, truth: np.ndarray) -> dict:
    n = int(mask.sum())
    if n == 0:
        return dict(n=0, tp=0.0, fp=0.0, yield_=0.0, dti=0.0)
    tp = float(kernel(ndi.distance_transform_edt(~mask)[truth]).sum())
    fp = float((1.0 - kernel(ndi.distance_transform_edt(~truth)[mask])).sum())
    fn = float(truth.sum()) - tp
    return dict(n=n, tp=round(tp, 2), fp=round(fp, 2), yield_=round(tp / n, 6),
                dti=round(tp / (tp + ALPHA * fp + BETA * fn + EPS), 6),
                coverage=round(tp / float(truth.sum()), 6))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "evidence/rmc_supervised_yield_20261031.json")
    ap.add_argument("--max-iter", type=int, default=200)
    ap.add_argument("--neg-pos", type=int, default=10)
    args = ap.parse_args()

    ctx = load_holdout_context(data_dir())
    foot, labels = ctx.foot, ctx.labels
    sgmc = ctx.sgmc_off & foot & ~labels
    quad = quadrant_ids(foot)

    chz = np.load(CACHE / "channels.npz")
    X = np.stack([chz[c][foot].astype(np.float32) for c in CHANNELS], axis=1)

    # random-placement reference yield on this truth set (no assumption, measured)
    rng = np.random.default_rng(7)
    rand = np.zeros(foot.shape, dtype=bool)
    fp_idx = np.flatnonzero(foot.ravel())
    rand.ravel()[rng.choice(fp_idx, size=37654, replace=False)] = True
    ref_random = yield_of(rand, sgmc)

    oof = np.zeros(foot.sum(), dtype=np.float32)
    aucs = []
    for q in FOLDS:
        test_2d = (quad == q) & foot
        forbidden = ndi.binary_dilation(test_2d, iterations=80)
        tr_elig = foot & ~forbidden
        y = np.zeros(foot.shape, dtype=bool)
        y[foot] = labels[foot]
        pos = np.flatnonzero((tr_elig & y)[foot])
        neg_pool = np.flatnonzero((tr_elig & ~y)[foot])
        n_neg = min(len(neg_pool), args.neg_pos * max(len(pos), 1))
        neg = np.sort(rng.choice(neg_pool, size=n_neg, replace=False))
        idx = np.concatenate([pos, neg])
        clf = HistGradientBoostingClassifier(
            max_iter=args.max_iter, learning_rate=0.08, max_leaf_nodes=31,
            l2_regularization=1.0, early_stopping=True, validation_fraction=0.12,
            random_state=20261031 + int(q))
        clf.fit(X[idx], np.concatenate([np.ones(len(pos), np.uint8), np.zeros(len(neg), np.uint8)]))
        te = np.flatnonzero(test_2d[foot])
        p = clf.predict_proba(X[te])[:, 1].astype(np.float32)
        oof[te] = p
        yt = y[foot][te]
        if yt.any():
            aucs.append({"quadrant": int(q), "n_train_pos": int(len(pos)),
                         "auc_within_quadrant_vs_labels": round(float(roc_auc_score(yt, p)), 4)})
        print(f"[loqo] quadrant {q}: trained on {len(pos)} pos / {len(neg)} neg")

    prop = np.zeros(foot.shape, dtype=np.float32)
    prop[foot] = oof
    np.save(CACHE / "propensity_loqo.npy", prop)
    d_lbl = ndi.distance_transform_edt(~labels)

    rows = {}
    rows["random_37654"] = ref_random
    # family-equivalent geometry, our surface
    for tag, field in (("sup", prop), ("unsup", np.load(CACHE / "surface.npy"))):
        elig = {
            "raw": foot,
            "b2": foot & (d_lbl > 2.0),
        }
        for ename, emask in elig.items():
            vals = np.where(emask, field, -1.0)
            for n in (37654, 60000, 120000):
                cut = np.partition(vals.ravel(), vals.size - n)[vals.size - n]
                dots = emask & (field >= cut)
                keep = int(dots.sum())
                if keep > n:
                    flat = np.flatnonzero(dots.ravel())
                    order = np.argsort(-vals.ravel()[flat])
                    sel = np.zeros(dots.size, dtype=bool)
                    sel[flat[order[:n]]] = True
                    dots = sel.reshape(dots.shape)
                rows[f"{tag}_{ename}_n{n}"] = yield_of(dots, sgmc)
                rows[f"{tag}_{ename}_n{n}"]["mean_rank_pct_of_top"] = None
    # corridor level sets from the supervised propensity, same instrument
    for frac in (0.0002, 0.0005, 0.001, 0.002, 0.005):
        k = int(round(frac * int(foot.sum())))
        vals = np.where(foot, prop, -1.0)
        cut = np.partition(vals.ravel(), vals.size - k)[vals.size - k]
        rows[f"sup_corridor_m{frac:g}"] = yield_of(foot & (prop >= cut), sgmc)

    best_key = max(rows, key=lambda k: rows[k]["yield_"])
    fam = {}
    led = ROOT / "evidence/ledger_instruments_20261031.json"
    if led.is_file():
        for r in json.loads(led.read_text())["rows"]:
            if r.get("status") != "measured" or not r.get("sgmc_coverage"):
                continue
            fam[r["site"] + " " + r["submission"][:28]] = {
                "dots": r["dots"],
                "yield": round(r["sgmc_coverage"] * int(ctx.sgmc_n_truth) / r["dots"], 6),
                "reported": r.get("reported"),
            }
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evidence_class": "DATA-MEASUREMENT + HOLDOUT-DTI (off-catalogue SGMC instrument, 62,703 px)",
        "yield_definition": "TP_w / N_emitted against USGS SGMC faults >300 m outside labels.tif",
        "random_reference_yield": ref_random,
        "family_yields_measured_from_pinned_bytes": fam,
        "loqo_fold_auc": aucs,
        "rows": rows,
        "best_row": best_key,
        "ok_to_submit": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1) + "\n")
    for k, v in rows.items():
        print(f"[yield] {k:>28} n={v['n']:>7} yield={v['yield_']:.4f} dti={v['dti']:.4f} cov={v.get('coverage',0):.4f}")
    print(f"[yield] wrote {args.out}; best = {best_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
