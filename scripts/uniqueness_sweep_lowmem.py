#!/usr/bin/env python3
"""Low-memory sweep of every *submission-shaped* GeoTIFF mirrored under /home/user/registry.

Same statistic as scripts/uniqueness_gate.py (share of the candidate's dots within 3 px of the
reference's dots, plus a subsampled Spearman), but: float32 reads, one raster at a time, incremental
JSONL so a killed run still leaves a usable receipt, and diagnostics/inputs/archive/bridge/external
trees skipped. Written 2026-10-31 after the 694-raster gate process died without output.
"""
from __future__ import annotations

import glob
import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[1]
CAND = ROOT / "docs/downloads/gemsass2-collar4hex-c4-b37636-sweep2-20261031T060500Z-zeros.tif"
OUT = ROOT / "evidence/uniqueness_collar4hex_submission_shaped_20261031.jsonl"
RADIUS, OVL, RHO = 3.0, 70.0, 0.90
SKIP = ("/docs/downloads/diagnostics/", "/inputs/", "/archive/", "/data/bridge/", "/data/external/",
         "/data/official/", "/.cache/")


def main() -> int:
    with rasterio.open(CAND) as ds:
        cand = ds.read(1, masked=False).astype(np.float32)
    cmask = cand > 0
    n = int(cmask.sum())
    refs = [p for p in sorted(glob.glob("/home/user/registry/**/*.tif", recursive=True))
            if not any(s in p for s in SKIP) and not p.endswith("-nan.tif")]
    out = open(OUT, "w")
    worst_ov, worst_rho, rows = 0.0, 0.0, 0
    for i, ref in enumerate(refs):
        try:
            with rasterio.open(ref) as ds:
                if ds.shape != cand.shape:
                    continue
                r = ds.read(1, masked=False).astype(np.float32)
            a = r.ravel()[::31].astype(np.float64)
            m = np.isfinite(r) & (r > 0)
            b = cand.ravel()[::31].astype(np.float64)
            ok = np.isfinite(a) & np.isfinite(b)
            rho = float(spearmanr(b[ok], a[ok]).correlation) if ok.sum() > 1000 else float("nan")
            del r, a, b, ok
            if int(m.sum()) == 0:
                continue
            d = ndi.distance_transform_edt(~m)
            ov = float((d[cmask] <= RADIUS).mean() * 100.0)
            del d, m
            rows += 1
            worst_ov = max(worst_ov, ov)
            rec = {"i": i, "ref": pathlib.Path(ref).name, "overlap_3px_pct": round(ov, 4),
                   "abs_spearman": None if not np.isfinite(rho) else round(abs(rho), 6)}
            out.write(json.dumps(rec) + "\n")
            if (i + 1) % 25 == 0:
                out.flush()
                print(f"{i+1}/{len(refs)} scanned worst_overlap={worst_ov:.2f}%", flush=True)
        except Exception as exc:  # a broken mirror file must not abort the sweep
            out.write(json.dumps({"i": i, "ref": pathlib.Path(ref).name, "error": str(exc)[:120]}) + "\n")
            out.flush()
    summary = {"candidate": CAND.name, "n_dots": n, "n_references": rows,
               "max_overlap_3px_pct": round(worst_ov, 4), "overlap_limit": OVL,
               "rho_limit": RHO, "note": "Spearman on a 1/31 subsample of every cell, as in the shared gate.",
               "passes_overlap_clause_worst_case": worst_ov <= OVL}
    out.write(json.dumps({"summary": summary}) + "\n")
    out.close()
    print(json.dumps(summary), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
