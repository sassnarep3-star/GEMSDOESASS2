#!/usr/bin/env python3
"""Rasterise the INGENIOUS / USGS Quaternary-fault trace database onto the 100 m
competition grid and compare it with the competition `labels.tif`.

Inputs (hash-pinned public mirrors, see registry/data_manifest.json):
  .cache/mirror/60GEMSDOE/data/external/trace_segments_utm11.csv     84,331 segments
  .cache/mirror/GEMSDOE24_old/data/external/gdr_qfaults_traces.csv   per-trace attributes

Outputs (git-ignored):
  .cache/work/qfaults_all.npy        bool  - every catalogued trace
  .cache/work/qfaults_labels.npy     bool  - competition labels.tif > 0
  .cache/work/catalogue_compare.json measured overlap statistics
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".cache/work"
MIRROR = ROOT / ".cache/mirror"


def grid_params(sample: Path):
    with rasterio.open(sample) as ds:
        t = ds.transform
        return ds.shape, float(t.c), float(t.a), float(t.f), float(t.e)


def rasterise_segments(seg_path: Path, attrs_path: Path, H, W, x0g, dx, y0g, dy, step_m=20.0):
    # trace_id -> attributes
    attrs = {}
    with attrs_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            attrs[row["trace_id"].strip()] = row
    grid = np.zeros((H, W), dtype=bool)
    per_recency = {}
    n_seg = 0
    with seg_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            n_seg += 1
            xa, ya, xb, yb = (float(row["x0"]), float(row["y0"]), float(row["x1"]), float(row["y1"]))
            L = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
            n = max(2, int(np.ceil(L / step_m)) + 1)
            xs = np.linspace(xa, xb, n)
            ys = np.linspace(ya, yb, n)
            cols = np.floor((xs - x0g) / dx).astype(np.int64)
            rows = np.floor((ys - y0g) / dy).astype(np.int64)
            ok = (rows >= 0) & (rows < H) & (cols >= 0) & (cols < W)
            grid[rows[ok], cols[ok]] = True
            rec = attrs.get(str(row["record_id"]).strip(), {}).get("recency", "?")
            per_recency.setdefault(rec, np.zeros((H, W), dtype=bool))[rows[ok], cols[ok]] = True
    return grid, per_recency, n_seg, attrs


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    (H, W), x0, dx, y0, dy = grid_params(ROOT / "data/bridge/sample_submission.tif")
    with rasterio.open(ROOT / "data/bridge/sample_submission.tif") as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/bridge/labels.tif") as ds:
        lab = ds.read(1)
    labels = (lab > 0) & footprint

    grid, per_recency, n_seg, attrs = rasterise_segments(
        MIRROR / "60GEMSDOE/data/external/trace_segments_utm11.csv",
        MIRROR / "GEMSDOE24_old/data/external/gdr_qfaults_traces.csv",
        H, W, x0, dx, y0, dy,
    )
    np.save(WORK / "qfaults_all.npy", grid)
    np.save(WORK / "qfaults_labels.npy", labels)
    np.save(WORK / "footprint.npy", footprint)

    for rec, arr in sorted(per_recency.items()):
        key = "".join(c if c.isalnum() else "_" for c in str(rec))[:40]
        np.save(WORK / f"qfaults_rec_{key}.npy", arr)

    def ov(a, b):
        return int(np.count_nonzero(a & b))

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "segments_read": n_seg,
        "traces": len(attrs),
        "footprint_cells": int(footprint.sum()),
        "labels_cells": int(labels.sum()),
        "qfaults_all_cells": int(grid.sum()),
        "labels_in_qfaults": ov(labels, grid),
        "labels_recall": round(ov(labels, grid) / max(1, int(labels.sum())), 6),
        "qfaults_precision": round(ov(labels, grid) / max(1, int(grid.sum())), 6),
        "per_recency": {
            str(k): {
                "cells": int(v.sum()),
                "labels_inside": ov(labels, v),
                "share_of_labels": round(ov(labels, v) / max(1, int(labels.sum())), 6),
            }
            for k, v in sorted(per_recency.items(), key=lambda kv: -int(kv[1].sum()))
        },
    }
    (WORK / "catalogue_compare.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
