#!/usr/bin/env python3
"""Score every hash-pinned / owner-reported raster against measurable proxy
truth sets, then test whether the proxy score explains the reported leaderboard
score better than dot count alone.

Proxy truth sets (all measurable, all derived from official public releases):
  P_SGMC2  USGS SGMC geologic-map faults that lie >= 2 px (200 m) outside the
           competition label raster  -- real mapped faults ABSENT from the
           catalogue everybody trained on.  Primary instrument.
  P_SGMC0  all SGMC faults (no buffer)
  P_LABELS the competition label raster itself (known-fault skill diagnostic;
           biased against collar-pruned submissions, reported for transparency)

Everything printed is a PROXY-HOLDOUT-DTI.  Reported scores are OWNER-REPORTED.
Nothing here is an organizer receipt.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems.metric import dti_binary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
REG = ROOT / ".cache/registry"


def load_raster(path: Path, footprint: np.ndarray):
    with rasterio.open(path) as ds:
        if ds.shape != footprint.shape:
            return None
        a = ds.read(1).astype(np.float64)
    a[~np.isfinite(a)] = 0.0
    a = np.clip(a, 0.0, 1.0)
    mask = (a > 0) & footprint
    return {"prob": a, "mask": mask, "n": int(mask.sum()), "sum_p": float(a[mask].sum())}


def build_truths(footprint, labels, sgmc):
    dil = lambda m, r: binary_dilation(m, np.ones((2 * r + 1, 2 * r + 1), dtype=bool))
    out = {}
    near2 = dil(labels, 2)
    out["P_SGMC2"] = (sgmc & ~near2 & footprint)
    near1 = dil(labels, 1)
    out["P_SGMC1"] = (sgmc & ~near1 & footprint)
    out["P_SGMC0"] = (sgmc & footprint)
    out["P_LABELS"] = labels & footprint
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "evidence/proxy_calibration.json"))
    args = ap.parse_args()

    footprint = np.load(WORK / "footprint.npy")
    labels = np.load(WORK / "qfaults_labels.npy")
    with rasterio.open(ROOT / ".cache/mirror/GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    truths = build_truths(footprint, labels, sgmc)
    tmeta = {k: int(v.sum()) for k, v in truths.items()}

    pins = json.loads((ROOT / "registry/fetch_pins.json").read_text())
    items = []
    for pin in pins:
        p = REG / f"{pin['key']}.tif"
        if p.is_file():
            items.append({"key": pin["key"], "reported": pin["reported"], "path": p,
                          "pin": "sha", "ref": pin["ref"]})
    anc = ROOT / "evidence/anchor_fetch_receipt.json"
    if anc.is_file():
        for r in json.loads(anc.read_text())["rows"]:
            if r.get("status") != "fetched":
                continue
            items.append({"key": r["site"], "reported": r["reported"], "path": ROOT / r["file"],
                          "pin": "head", "ref": "HEAD"})

    rows = []
    for it in items:
        r = load_raster(it["path"], footprint)
        if r is None:
            rows.append({**{k: it[k] for k in ("key", "reported", "pin")}, "status": "shape_mismatch"})
            continue
        row = {"key": it["key"], "reported": it["reported"], "pin": it["pin"], "ref": it["ref"],
               "file": str(it["path"].relative_to(ROOT)), "dots": r["n"], "sum_p": round(r["sum_p"], 1)}
        for name, T in truths.items():
            d = dti_binary(r["mask"], T, footprint)
            row[name] = round(d["dti"], 6)
            row[name + "_T"] = round(d["T"], 1)
        rows.append(row)
        print(f"{row['key']:12s} {row['reported']:.4f} N={row['dots']:7d} "
              + "  ".join(f"{k}={row[k]:.5f}" for k in truths))

    rows = [r for r in rows if "status" not in r]
    rep = np.array([r["reported"] for r in rows])
    corr = {}
    for k in list(truths) + ["dots"]:
        v = np.array([r[k] for r in rows])
        rho, p = spearmanr(v, rep)
        corr[k] = {"spearman": float(rho), "p": float(p), "n": len(rows)}

    # leave-one-out linear fit: reported ~ a + b*proxy
    fits = {}
    for k in list(truths) + ["dots"]:
        X = np.array([r[k] for r in rows], dtype=float)
        Xd = np.column_stack([np.ones_like(X), X])
        errs = []
        for i in range(len(rows)):
            m = np.ones(len(rows), bool)
            m[i] = False
            beta, *_ = np.linalg.lstsq(Xd[m], rep[m], rcond=None)
            errs.append(rep[i] - Xd[i] @ beta)
        errs = np.array(errs)
        ss_res = float((errs ** 2).sum())
        ss_tot = float(((rep - rep.mean()) ** 2).sum())
        beta, *_ = np.linalg.lstsq(Xd, rep, rcond=None)
        fits[k] = {"slope": float(beta[1]), "intercept": float(beta[0]),
                   "loo_r2": 1 - ss_res / ss_tot if ss_tot > 0 else None,
                   "loo_rmse": float(np.sqrt(ss_res / len(errs)))}

    out = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "label": "PROXY-HOLDOUT-DTI (measurable proxy truth) vs OWNER-REPORTED leaderboard score",
        "truth_sets": tmeta,
        "n_items": len(rows),
        "correlations": corr,
        "leave_one_out_linear_fits": fits,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"truth_sets": tmeta, "correlations": corr, "fits": fits}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
