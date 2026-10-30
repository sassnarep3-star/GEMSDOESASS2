#!/usr/bin/env python3
"""Pairwise 3 px dot-overlap matrix for the nine focus sites, the sparse candidate and the lattice.

Uses the same dot rule and 3 px KD-tree test as ``scripts/focus_uniqueness_check.py`` (imported,
not re-implemented). Cell (row i, column j) is the fraction of row-i dots lying within 3 px of
some column-j dot. The lattice is reported separately because it is a space-filling raster: the
literal lane rule ("more than 70% of your dots within 3 px of one registry raster") is evaluated
against it without exemption here.

Also tests exact-pixel set inclusion (is every dot of A also a dot of B?) for lineage claims.

Usage:
  python scripts/focus_pairwise_matrix.py --registry ~/.cache/registry_pinned \  (flat repo__file copies from fetch_pinned_registry.py)
      --sample data/bridge/sample_submission.tif --out evidence/focus_pairwise_matrix_20261030.json \
      --candidate docs/downloads/<file>.tif
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from focus_uniqueness_check import OVERLAP_LIMIT, dots_of, overlap_3px, sha256_file  # noqa: E402

FOCUS = {
    "GEMSDOE24": "GEMSDOE24/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
    "GEMSDOE25": "GEMSDOE25/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
    "GEMSDOE27": "GEMSDOE27/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
    "GEMSDOE28": "GEMSDOE28/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
    "GEMSDOE30": "GEMSDOE30/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "GEMSDOE31/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
    "GEMSDOE32": "GEMSDOE32/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "GEMSDOE36/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}
LATTICE = "GEMSDOE24/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--sample", required=True, type=Path)
    p.add_argument("--candidate", action="append", type=Path, default=[])
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    with rasterio.open(args.sample) as ref:
        footprint = np.isfinite(ref.read(1)) & (ref.read_masks(1) > 0)

    sets: dict[str, dict] = {}
    for name, rel in FOCUS.items():
        path = args.registry / f"{name}__{Path(rel).name}"
        arr = rasterio.open(path).read(1).astype(np.float32)
        sets[name] = {"path": str(path), "sha256": sha256_file(path), "mask": dots_of(arr, footprint)}
    for cand in args.candidate:
        arr = rasterio.open(cand).read(1).astype(np.float32)
        sets[cand.name] = {"path": str(cand), "sha256": sha256_file(cand), "mask": dots_of(arr, footprint)}
    lat_path = args.registry / f"GEMSDOE24__{Path(LATTICE).name}"
    lat_arr = rasterio.open(lat_path).read(1).astype(np.float32)
    lattice_mask = dots_of(lat_arr, footprint)

    coords = {k: np.argwhere(v["mask"])[:, ::-1].astype(np.float64) for k, v in sets.items()}
    lat_coords = np.argwhere(lattice_mask)[:, ::-1].astype(np.float64)

    names = list(sets)
    matrix = {}
    for a in names:
        row = {}
        for b in names:
            if a == b:
                continue
            row[b] = round(overlap_3px(coords[a], coords[b]), 6)
        matrix[a] = row

    lattice_overlap = {k: round(overlap_3px(coords[k], lat_coords), 6) for k in names}
    subsets = {}
    for a in names:
        for b in names:
            if a == b:
                continue
            extra = int((sets[a]["mask"] & ~sets[b]["mask"]).sum())
            if extra == 0:
                subsets[f"{a} subset_of {b}"] = {"dots": int(sets[a]["mask"].sum())}

    summary = {
        k: {
            "sha256": v["sha256"],
            "dots": int(v["mask"].sum()),
            "max_overlap_vs_other_focus_or_candidate": max(matrix[k].values()) if matrix[k] else None,
            "max_overlap_peer": max(matrix[k], key=matrix[k].get) if matrix[k] else None,
            "overlap_vs_lattice_3px": lattice_overlap[k],
            "literal_lattice_gate_70pct_pass": lattice_overlap[k] <= OVERLAP_LIMIT,
        }
        for k, v in sets.items()
    }
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sample_sha256": sha256_file(args.sample),
        "lattice": {"file": LATTICE, "sha256": sha256_file(lat_path), "dots": int(lattice_mask.sum())},
        "dot_rule": "finite, >0, inside the sample footprint (scripts/focus_uniqueness_check.py)",
        "overlap_limit": OVERLAP_LIMIT,
        "radius_px": 3.0,
        "summary": summary,
        "pairwise_overlap_3px": matrix,
        "exact_pixel_subset_relations": subsets,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    for k in names:
        s = summary[k]
        print(f"{k:45s} dots={s['dots']:6d} max_peer={s['max_overlap_vs_other_focus_or_candidate']:.4f} "
              f"lattice={s['overlap_vs_lattice_3px']:.4f} literal_lattice_pass={s['literal_lattice_gate_70pct_pass']}")
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
