#!/usr/bin/env python3
"""H-CORRIDOR hypothesis — train a lineament/fault-probability model on the
competition's own label raster and emit a narrow graded corridor along the
resulting high-probability traces.

Why this is a different mechanism from the whole nine-site family
(measured in evidence/nine_site_forensics.json and
evidence/proxy_calibration.json): every focus-site raster is an isolated-dot
lattice of 37k-61k cells spaced ~1.2 km apart.  Under the official metric
    DTI = TP_w / (0.2*TP_w + 0.2*FP_w + 0.8*|G|)
a pixel emitted ON a fault earns credit from every truth pixel within 300 m and
pays a false-positive cost of (1 - k(d)) that falls to zero as the line
approaches the trace.  Contiguous emission along a probable trace is the shape
the metric rewards; no file in the family has that shape.

Leakage control: the two catalogue rasters in the cube (qfv = GDR Quaternary
fault raster, univariate AUC 0.984 against the labels; sgm = SGMC, the proxy
truth itself) are dropped before training.  Everything else is an independent
geophysical / geometric field.

Outputs (git-ignored): .cache/work/cand_prob.f32 (probability map),
.cache/work/cand_model.json (receipt).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, sobel

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
LEAKAGE_PREFIXES = ("qfv:", "sgm:")


def block_stack(src, idxs, r0, r1):
    """Gather src[idxs, r0:r1, :] band by band (never materialises the full cube)."""
    out = np.empty((len(idxs), r1 - r0, src.shape[2]), np.float32)
    for k, i in enumerate(idxs):
        out[k] = src[i, r0:r1, :]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(WORK / "cand_prob.f32"))
    ap.add_argument("--neg", type=int, default=250_000)
    args = ap.parse_args()

    meta = json.loads((WORK / "cube_meta.json").read_text())
    names = meta["band_names"]
    H, W = meta["grid"]["shape"]
    keep = [i for i, n in enumerate(names) if not n.startswith(LEAKAGE_PREFIXES)]
    print("bands", len(names), "->", len(keep), "after dropping",
          [n for n in names if n.startswith(LEAKAGE_PREFIXES)], flush=True)
    cube = np.lib.format.open_memmap(WORK / "cube.f32", mode="r", dtype=np.float32, shape=(len(names), H, W))
    footprint = np.load(WORK / "footprint.npy")
    labels = np.load(WORK / "qfaults_labels.npy")

    base = {"rtp": names.index("f:rtp"), "tmi": names.index("f:tmi"),
            "det_elev": names.index("f:det_elev"), "grav": names.index("f:iso_grav_anom"),
            "tc": names.index("f:tc"), "strain": names.index("f:geod_2ndinv")}
    deriv_path = WORK / "deriv.f32"
    deriv_names = [f"d:{k}_{s}" for k in base for s in ("coh", "energy")]
    if deriv_path.is_file() and deriv_path.stat().st_size == 4 * 2 * len(base) * H * W:
        deriv = np.lib.format.open_memmap(deriv_path, mode="r", dtype=np.float32,
                                          shape=(2 * len(base), H, W))
        print("reusing cached derived bands", deriv_names, flush=True)
    else:
        deriv = np.lib.format.open_memmap(deriv_path, mode="w+", dtype=np.float32,
                                          shape=(2 * len(base), H, W))
        d = 0
        for key, bi in base.items():
            a = np.array(cube[bi], dtype=np.float32)
            a[~np.isfinite(a)] = 0.0
            gx = sobel(a, axis=1).astype(np.float32)
            gy = sobel(a, axis=0).astype(np.float32)
            jxx = gaussian_filter(gx * gx, 1.5)
            jyy = gaussian_filter(gy * gy, 1.5)
            jxy = gaussian_filter(gx * gy, 1.5)
            del gx, gy
            tr = jxx + jyy
            detq = jxx * jyy - jxy * jxy
            del jxx, jyy, jxy
            gap = np.sqrt(np.maximum(tr * tr - 4 * detq, 0.0))
            l1 = 0.5 * (tr + gap)
            l2 = 0.5 * (tr - gap)
            deriv[d] = np.where(l1 > 0, (l1 - l2) / np.maximum(l1 + l2, 1e-12), 0.0)
            deriv[d + 1] = np.sqrt(np.maximum(tr, 0.0))
            del tr, detq, gap, l1, l2, a
            d += 2
            print("  derived", key, flush=True)
        deriv.flush()

    nfeat = len(keep) + deriv.shape[0]
    feat_names = [names[i] for i in keep] + deriv_names

    rng = np.random.default_rng(20261031)
    pos = np.flatnonzero(labels.ravel())
    neg_pool = np.flatnonzero((~labels & footprint).ravel())
    neg = rng.choice(neg_pool, size=min(args.neg, neg_pool.size), replace=False)
    idx = np.concatenate([pos, neg])
    y = np.concatenate([np.ones(pos.size, np.uint8), np.zeros(neg.size, np.uint8)])
    rr, cc = np.unravel_index(idx, (H, W))
    order = np.argsort(rr, kind="stable")
    rr, cc, y = rr[order], cc[order], y[order]
    X = np.empty((idx.size, nfeat), np.float32)
    start = 0
    for r0 in range(0, H, 150):
        r1 = min(r0 + 150, H)
        sel = (rr >= r0) & (rr < r1)
        if not sel.any():
            continue
        sr, sc = rr[sel] - r0, cc[sel]
        blk = block_stack(cube, keep, r0, r1)
        dblk = np.asarray(deriv[:, r0:r1, :], dtype=np.float32)
        n = int(sel.sum())
        X[start:start + n, :len(keep)] = blk[:, sr, sc].T
        X[start:start + n, len(keep):] = dblk[:, sr, sc].T
        start += n
        del blk, dblk
    assert start == idx.size
    print("training matrix", X.shape, "positives", int(y.sum()), flush=True)

    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.metrics import roc_auc_score
    clf = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                              max_leaf_nodes=31, l2_regularization=1.0,
                                              random_state=7)
    clf.fit(X, y)
    auc_train = float(roc_auc_score(y, clf.predict_proba(X)[:, 1]))
    print("in-sample AUC", round(auc_train, 4), flush=True)
    from sklearn.inspection import permutation_importance
    sub = rng.choice(X.shape[0], size=40_000, replace=False)
    pi = permutation_importance(clf, X[sub], y[sub], n_repeats=3, random_state=7,
                                scoring="roc_auc", n_jobs=2)
    importances = sorted(zip(feat_names, pi.importances_mean.tolist()), key=lambda kv: -kv[1])[:20]
    print("permutation-importance AUC drop (40k subsample) computed", flush=True)

    out = np.lib.format.open_memmap(args.out, mode="w+", dtype=np.float32, shape=(H, W))
    for r0 in range(0, H, 150):
        r1 = min(r0 + 150, H)
        blk = block_stack(cube, keep, r0, r1).reshape(len(keep), -1).T
        dblk = np.asarray(deriv[:, r0:r1, :], dtype=np.float32).reshape(deriv.shape[0], -1).T
        Xb = np.empty((blk.shape[0], nfeat), np.float32)
        Xb[:, :len(keep)] = blk
        Xb[:, len(keep):] = dblk
        out[r0:r1, :] = clf.predict_proba(Xb)[:, 1].astype(np.float32).reshape(r1 - r0, W)
        del blk, dblk, Xb
    out.flush()
    print("wrote", args.out, flush=True)

    (WORK / "cand_model.json").write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "n_features": nfeat,
        "dropped_as_leakage": [n for n in names if n.startswith(LEAKAGE_PREFIXES)],
        "feature_names": feat_names,
        "train_positives": int(y.sum()),
        "train_negatives": int((y == 0).sum()),
        "in_sample_auc": auc_train,
        "top_features": [(n, round(v, 5)) for n, v in importances],
        "model": "HistGradientBoostingClassifier(max_iter=300, lr=0.06, leaves=31, l2=1.0, seed=7)",
    }, indent=2) + "\n", encoding="utf-8")
    print("top features", [(n, round(v, 4)) for n, v in importances][:12], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
