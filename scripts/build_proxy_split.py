#!/usr/bin/env python3
"""Split the INGENIOUS Quaternary-fault trace database into a VISIBLE part (the
traces that appear in the competition's own label raster) and a HIDDEN part (the
traces that do not).  HIDDEN is our measurable stand-in for the competition's
secret test truth: real faults that are absent from the labels everybody had.

Protocol conformance (standing prompt §2 / §4):
  * whole *fault traces* are withheld, never random pixels;
  * a buffer of ambiguous traces is dropped from both sides;
  * every catalogue-derived feature may use VISIBLE only.

Outputs (git-ignored, .cache/work/):
  qf_visible.npy   bool  traces present in labels.tif
  qf_hidden.npy    bool  traces absent from labels.tif   <-- proxy test truth
  qf_ambiguous.npy bool  dropped buffer
  proxy_split.json measured receipt
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
MIRROR = ROOT / ".cache/mirror"
STEP_M = 20.0
COVER_VISIBLE = 0.50   # trace fully covered by labels -> it IS in the public catalogue
COVER_HIDDEN = 0.05    # trace essentially absent      -> withhold as proxy truth


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as ds:
        H, W = ds.shape
        t = ds.transform
        x0, dx, y0, dy = float(t.c), float(t.a), float(t.f), float(t.e)
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        labels = (ds.read(1) > 0) & footprint

    per_trace = defaultdict(lambda: [0, 0])  # tid -> [cells, cells_in_labels]
    with (MIRROR / "60GEMSDOE/data/external/trace_segments_utm11.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            tid = str(r["record_id"]).strip()
            xa, ya, xb, yb = float(r["x0"]), float(r["y0"]), float(r["x1"]), float(r["y1"])
            L = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
            n = max(2, int(np.ceil(L / STEP_M)) + 1)
            cols = np.floor((np.linspace(xa, xb, n) - x0) / dx).astype(np.int64)
            rows = np.floor((np.linspace(ya, yb, n) - y0) / dy).astype(np.int64)
            ok = (rows >= 0) & (rows < H) & (cols >= 0) & (cols < W)
            rows, cols = rows[ok], cols[ok]
            if rows.size == 0:
                continue
            rec = per_trace[tid]
            rec[0] += int(rows.size)
            rec[1] += int(labels[rows, cols].sum())

    klass = {}
    for tid, (cells, inlab) in per_trace.items():
        frac = inlab / max(1, cells)
        if frac >= COVER_VISIBLE:
            klass[tid] = "visible"
        elif frac <= COVER_HIDDEN:
            klass[tid] = "hidden"
        else:
            klass[tid] = "ambiguous"

    grids = {k: np.zeros((H, W), dtype=bool) for k in ("visible", "hidden", "ambiguous")}
    with (MIRROR / "60GEMSDOE/data/external/trace_segments_utm11.csv").open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            tid = str(r["record_id"]).strip()
            k = klass.get(tid)
            if k is None:
                continue
            xa, ya, xb, yb = float(r["x0"]), float(r["y0"]), float(r["x1"]), float(r["y1"])
            L = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
            n = max(2, int(np.ceil(L / STEP_M)) + 1)
            cols = np.floor((np.linspace(xa, xb, n) - x0) / dx).astype(np.int64)
            rows = np.floor((np.linspace(ya, yb, n) - y0) / dy).astype(np.int64)
            ok = (rows >= 0) & (rows < H) & (cols >= 0) & (cols < W)
            grids[k][rows[ok], cols[ok]] = True

    vis, hid, amb = grids["visible"], grids["hidden"], grids["ambiguous"]
    vis &= footprint
    hid &= footprint
    amb &= footprint
    # Traces of different classes can cross; keep the split disjoint and drop the overlap.
    both = vis & hid
    vis &= ~both
    hid &= ~both
    amb |= both
    # Buffer: hidden truth cells that sit on/next to a visible trace are ambiguous
    # (the real test truth is "not in the catalogue", so keep them but record them).
    from scipy.ndimage import binary_dilation
    near_vis = binary_dilation(vis, np.ones((7, 7), dtype=bool))
    hid_near_vis = hid & near_vis

    np.save(WORK / "qf_visible.npy", vis)
    np.save(WORK / "qf_hidden.npy", hid)
    np.save(WORK / "qf_ambiguous.npy", amb)

    counts = {k: int(np.count_nonzero(v)) for k, v in
              (("visible", vis), ("hidden", hid), ("ambiguous", amb))}
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "rule": {"visible_if_label_coverage_ge": COVER_VISIBLE,
                 "hidden_if_label_coverage_le": COVER_HIDDEN,
                 "dropped": "traces in between, plus cells where a visible and a hidden trace overlap"},
        "traces": {k: sum(1 for v in klass.values() if v == k) for k in ("visible", "hidden", "ambiguous")},
        "cells": counts,
        "labels_cells": int(labels.sum()),
        "labels_inside_visible": int(np.count_nonzero(labels & vis)),
        "labels_inside_hidden": int(np.count_nonzero(labels & hid)),
        "hidden_cells_within_3px_of_visible": int(np.count_nonzero(hid & near_vis)),
        "hidden_cells_clean": int(np.count_nonzero(hid & ~near_vis)),
    }
    (WORK / "proxy_split.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
