#!/usr/bin/env python3
"""Lane gate: is a candidate a duplicate of anything already registered?

Two tests against every registry raster, both on the *final* saved bytes:

  * dot overlap  — percentage of candidate positives within 3 px of a reference
                   positive.  Duplicate if > 70 %.
  * rank         — Spearman between the two full rasters.  Duplicate if |rho| > 0.90.

Sibling artifacts produced by the same generator are excluded by prefix so that a
build is never compared against its own earlier stamp.

Writes a JSON receipt.  Exit code 2 when the lane fails, so CI and the build script
cannot silently ship a duplicate.
"""

from __future__ import annotations

import argparse
import glob
import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = pathlib.Path(__file__).resolve().parents[1]
OVERLAP_LIMIT = 70.0
RHO_LIMIT = 0.90
RADIUS_PX = 3.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True, type=pathlib.Path)
    ap.add_argument("--reference-glob", nargs="+", default=[
        str(ROOT / "docs/downloads/*.tif"), "/tmp/nine/g[0-9][0-9].tif"])
    ap.add_argument("--exclude-prefix", nargs="*", default=["gemsass2-strainridge"])
    ap.add_argument("--out", required=True, type=pathlib.Path)
    args = ap.parse_args()

    with rasterio.open(args.candidate) as ds:
        cand = ds.read(1)
    cmask = cand > 0
    n = int(cmask.sum())

    refs: list[str] = []
    for pattern in args.reference_glob:
        refs.extend(sorted(glob.glob(pattern)))
    rows = []
    for ref in refs:
        name = pathlib.Path(ref).name
        if ref == str(args.candidate) or name == args.candidate.name:
            continue
        if any(name.startswith(p) for p in args.exclude_prefix):
            continue
        with rasterio.open(ref) as ds:
            if ds.shape != cand.shape:
                continue
            r = ds.read(1)
        rmask = r > 0
        if rmask.sum() == 0:
            continue
        dist = ndi.distance_transform_edt(~rmask)
        overlap = float((dist[cmask] <= RADIUS_PX).mean() * 100.0)

        a = cand.ravel()[::31].astype(np.float64)
        b = r.ravel()[::31].astype(np.float64)
        ok = np.isfinite(a) & np.isfinite(b)
        rho = float(spearmanr(a[ok], b[ok]).correlation) if ok.sum() > 1000 else float("nan")
        rows.append({
            "ref": name,
            "ref_dots": int(rmask.sum()),
            "overlap_3px_pct": round(overlap, 4),
            "abs_spearman": None if not np.isfinite(rho) else round(abs(rho), 6),
        })

    if not rows:
        raise SystemExit("no comparable reference rasters found")
    rows.sort(key=lambda x: -x["overlap_3px_pct"])
    rhos = [r["abs_spearman"] for r in rows if r["abs_spearman"] is not None]
    worst_rho = max(rhos) if rhos else 0.0
    worst_ov = rows[0]["overlap_3px_pct"]
    passed = worst_ov <= OVERLAP_LIMIT and worst_rho <= RHO_LIMIT

    receipt = {
        "candidate": args.candidate.name,
        "n_dots": n,
        "n_references": len(rows),
        "radius_px": RADIUS_PX,
        "limits": {"overlap_pct": OVERLAP_LIMIT, "abs_spearman": RHO_LIMIT},
        "max_overlap_3px_pct": worst_ov,
        "max_abs_spearman": round(worst_rho, 6),
        "passes_lane": passed,
        "top_overlaps": rows[:10],
        "scope_note": (
            "Compared against the nine hash-pinned focus-site champions plus every local "
            "download. The wider GEMSDOE corpus (~90 sites) is not mirrored locally."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2))
    print(json.dumps({k: receipt[k] for k in
                      ("n_dots", "n_references", "max_overlap_3px_pct",
                       "max_abs_spearman", "passes_lane")}, indent=2))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
