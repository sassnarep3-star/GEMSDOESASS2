#!/usr/bin/env python3
"""Experiment 3 + final artifact builder.

Sweep the two knobs that control the trade the official metric actually makes --
*enrichment strength* (how strongly the emission follows the probability model)
and *minimum separation* (how far the emission spreads) -- at the champion's exact
emitted mass, and pick the best by the measurable proxy instrument.

Selection rule (pre-registered before the sweep is read):
    maximise  P_SGMC2  subject to  P_LABELS <= champion's P_LABELS (0.0067)
                                   and  emitted mass == 37,654
If nothing beats the champion's P_SGMC2 = 0.09469, the best candidate is shipped
anyway and the shortfall is reported as a negative result.

Writes the submission GeoTIFFs (zeros-outside and nan-outside) plus a zip of each.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, maximum_filter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems.metric import dti_probabilistic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
REG = ROOT / ".cache/registry"
OUT = ROOT / "docs/downloads"
MASS = 37654
CHAMP_SGMC2 = 0.094686
CHAMP_LABELS = 0.006709

STEM = "gemsass2-hcorr-lineament-offcat-37654-20261031T000000Z"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def greedy(score: np.ndarray, allowed: np.ndarray, sep: int, k: int, H, W):
    """Non-max suppression (window 2*sep+1) then greedy top-score with exclusion."""
    peak = maximum_filter(score, size=2 * sep + 1) if sep else score
    cand = np.flatnonzero(allowed.ravel() & (score >= peak - 1e-12).ravel())
    cand = cand[np.argsort(-score.ravel()[cand], kind="stable")]
    emit = np.zeros((H, W), np.float32)
    taken = np.zeros((H, W), bool)
    n = 0
    for idx in cand:
        if n >= k:
            break
        r, c = divmod(int(idx), W)
        if taken[r, c]:
            continue
        emit[r, c] = 1.0
        r0, r1 = max(0, r - sep), min(H, r + sep + 1)
        c0, c1 = max(0, c - sep), min(W, c + sep + 1)
        taken[r0:r1, c0:c1] = True
        n += 1
    return emit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=str(OUT))
    args = ap.parse_args()

    meta = json.loads((WORK / "cube_meta.json").read_text())
    H, W = meta["grid"]["shape"]
    footprint = np.load(WORK / "footprint.npy")
    labels = np.load(WORK / "qfaults_labels.npy")
    prob = np.asarray(np.lib.format.open_memmap(
        WORK / "cand_prob.f32", mode="r", dtype=np.float32, shape=(H, W))).astype(np.float64)
    prob[~footprint] = 0.0
    with rasterio.open(ROOT / ".cache/mirror/GEMSDOE30/data/external/derived_sgmc_faults_100m_u8.tif") as ds:
        sgmc = ds.read(1) > 0
    near2 = binary_dilation(labels, np.ones((5, 5), bool))
    truths = {"P_SGMC2": sgmc & ~near2 & footprint,
              "P_SGMC0": sgmc & footprint,
              "P_LABELS": labels & footprint}

    with rasterio.open(REG / "GEMSDOE32.tif") as ds:
        champ = ds.read(1).astype(np.float64)
    champ[~np.isfinite(champ)] = 0.0

    def score_row(name, emit, extra=None):
        e = np.clip(emit, 0.0, 1.0)
        row = {"emission": name, "sum_p": round(float(e[footprint].sum()), 1),
               "nonzero_px": int((e[footprint] > 0).sum())}
        for tn, T in truths.items():
            row[tn] = round(float(dti_probabilistic(e, T, footprint)["dti"]), 6)
        if extra:
            row.update(extra)
        print(json.dumps(row), flush=True)
        return row

    rows = [score_row("CHAMPION_GEMSDOE32_reference", champ, {"role": "reference"})]

    pm = prob.max()
    pn = np.clip(prob / pm, 1e-9, 1.0)
    for collar in (2, 3):
        allowed = footprint & ~binary_dilation(labels, np.ones((2 * collar + 1, 2 * collar + 1), bool))
        for alpha in (0.0, 0.5, 1.0, 2.0):
            s = np.ones_like(pn) if alpha == 0 else pn ** alpha
            for sep in (3, 6, 9, 12):
                e = greedy(s, allowed, sep, MASS, H, W)
                if e.sum() < MASS * 0.98:
                    print(f"skip alpha={alpha} sep={sep} collar={collar}: only {int(e.sum())} cells", flush=True)
                    continue
                rows.append(score_row(f"a{alpha}_sep{sep}_c{collar}", e,
                                      {"alpha": alpha, "sep": sep, "collar": collar,
                                       "dots": int(e.sum())}))

    elig = [r for r in rows if r["emission"] != "CHAMPION_GEMSDOE32_reference"
            and r["P_LABELS"] <= CHAMP_LABELS + 1e-9 and r["sum_p"] >= MASS * 0.98]
    elig.sort(key=lambda r: -r["P_SGMC2"])
    best = elig[0] if elig else None
    verdict = {
        "rule": "max P_SGMC2 s.t. P_LABELS <= 0.006709 and emitted mass == 37654",
        "n_candidates": len(rows) - 1,
        "n_eligible": len(elig),
        "champion_P_SGMC2": CHAMP_SGMC2,
        "best_P_SGMC2": best["P_SGMC2"] if best else None,
        "beats_champion_on_proxy": bool(best and best["P_SGMC2"] > CHAMP_SGMC2),
        "shortfall_pct": (round(100 * (1 - best["P_SGMC2"] / CHAMP_SGMC2), 2) if best else None),
    }
    print(json.dumps(verdict, indent=2), flush=True)
    if best is None:
        raise SystemExit("no eligible candidate")

    # ---------------- rebuild the winner and write the artifacts ----------------
    collar = int(best["collar"])
    alpha = float(best["alpha"])
    sep = int(best["sep"])
    allowed = footprint & ~binary_dilation(labels, np.ones((2 * collar + 1, 2 * collar + 1), bool))
    s = np.ones_like(pn) if alpha == 0 else pn ** alpha
    emit = greedy(s, allowed, sep, MASS, H, W)
    emit = np.where(footprint, np.clip(emit, 0.0, 1.0), 0.0).astype(np.float32)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as ds:
        profile = ds.profile.copy()
        sample = ds.read(1)
    outside = ~np.isfinite(sample)
    profile.update(driver="GTiff", count=1, dtype="float32", compress="deflate",
                   predictor=2, nodata=None, tiled=False)
    written = []
    for tag, arr in (("zeros", np.where(outside, 0.0, emit)),
                     ("nan", np.where(outside, np.nan, emit))):
        p = outdir / f"{STEM}-{tag}.tif"
        with rasterio.open(p, "w", **profile) as dst:
            dst.write(arr.astype(np.float32), 1)
            dst.set_band_description(1, "fault probability")
        z = outdir / f"{STEM}-{tag}.zip"
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(p, arcname=p.name)
        written.append({"tag": tag, "tif": p.name, "bytes": p.stat().st_size,
                        "sha256": sha256_file(p), "zip": z.name,
                        "zip_bytes": z.stat().st_size, "zip_sha256": sha256_file(z)})

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "stem": STEM,
        "selection": verdict,
        "winner": best,
        "sweep": rows,
        "emission": {"alpha": alpha, "min_separation_px": sep, "catalogue_collar_px": collar,
                     "emitted_mass": float(emit.sum()),
                     "nonzero_pixels": int((emit > 0).sum())},
        "files": written,
        "label": "PROXY-HOLDOUT-DTI on measurable proxy truth; NOT an organizer score",
    }
    (ROOT / "evidence/hcorr_sweep_and_artifact.json").write_text(json.dumps(receipt, indent=2) + "\n",
                                                                 encoding="utf-8")
    print(json.dumps(written, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
