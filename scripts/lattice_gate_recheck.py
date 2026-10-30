#!/usr/bin/env python3
"""Recheck the literal 70 % lattice rule for candidate GeoTIFFs and write a JSON receipt.

Why this exists: an earlier run card reported ``passes_lane: true`` for a sparse candidate. That
result came from a gate that exempts any raster whose name contains "lattice" (the "space-filling
probe" rule). This script applies the literal rule with no exemption, measures the candidate
against the pinned 13GEMSDOE lattice, and records where the only cells that could satisfy the rule
are located.

Measures, all on saved bytes:
  * dots of the lattice and of each candidate (finite, > 0, inside the sample footprint);
  * share of each candidate's dots within 3 px of any lattice dot (KD-tree, same as the repo gate);
  * the footprint cells farther than 3 px from every lattice dot, and their distance to the
    footprint edge (the only places where a dot would not overlap the lattice);
  * the strict local format verdict (``scripts/validate_tif.py``) for each candidate.

It performs no placement, no holdout and no submission. Requires the lattice file from
``scripts/fetch_pinned_registry.py`` (flat copy ``GEMSDOE24__13gems_...tif`` in ``--registry``).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from focus_uniqueness_check import OVERLAP_LIMIT, dots_of, overlap_3px, sha256_file  # noqa: E402
from validate_tif import validate  # noqa: E402

LATTICE_NAME = "GEMSDOE24__13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--registry", required=True, type=Path)
    p.add_argument("--sample", type=Path, default=ROOT / "data/bridge/sample_submission.tif")
    p.add_argument("--candidate", action="append", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()

    with rasterio.open(args.sample) as ref:
        footprint = np.isfinite(ref.read(1)) & (ref.read_masks(1) > 0)
    lat_path = args.registry / LATTICE_NAME
    lat_mask = dots_of(rasterio.open(lat_path).read(1).astype(np.float32), footprint)
    lat_coords = np.argwhere(lat_mask)[:, ::-1].astype(np.float64)

    # Footprint cells farther than 3 px from every lattice dot.
    dist_to_lattice = ndimage.distance_transform_edt(~lat_mask)
    far = footprint & (dist_to_lattice > 3.0)
    edge = footprint & ~ndimage.binary_erosion(footprint, iterations=1)
    dist_to_edge = ndimage.distance_transform_edt(~edge)
    far_dist_edge = dist_to_edge[far]

    candidates = []
    for cand in args.candidate:
        cand = cand.expanduser().resolve()
        arr = rasterio.open(cand).read(1).astype(np.float32)
        cmask = dots_of(arr, footprint)
        ccoords = np.argwhere(cmask)[:, ::-1].astype(np.float64)
        ov = overlap_3px(ccoords, lat_coords)
        # Minimum dots that would have to sit in far cells to reach the limit: n_far >= (1-limit)*n.
        min_far_needed = int(np.ceil((1 - OVERLAP_LIMIT) * len(ccoords)))
        verdict = validate(cand, args.sample)
        candidates.append({
            "file": cand.name,
            "sha256": sha256_file(cand),
            "dots": int(cmask.sum()),
            "overlap_vs_lattice_3px": round(ov, 6),
            "literal_lattice_gate_pass": bool(ov <= OVERLAP_LIMIT),
            "dots_needed_in_far_cells_to_pass": min_far_needed,
            "far_cells_available": int(far.sum()),
            "far_cells_can_satisfy_rule": bool(far.sum() >= min_far_needed),
            "validator_strict_local_format_pass": bool(verdict["strict_local_format_pass"]),
            "validator_checks": verdict["checks"],
        })

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope": "Literal rule, no name-based exemption. Measurement on saved bytes. Not an organizer "
                 "receipt; no holdout; no placement; no submission.",
        "limit_overlap_3px": OVERLAP_LIMIT,
        "lattice": {"file": LATTICE_NAME, "sha256": sha256_file(lat_path), "dots": int(lat_mask.sum())},
        "footprint_cells": int(footprint.sum()),
        "footprint_cells_farther_than_3px_from_lattice": int(far.sum()),
        "far_cells_min_distance_to_footprint_edge_px": {
            "min": float(far_dist_edge.min()) if far.any() else None,
            "max": float(far_dist_edge.max()) if far.any() else None,
        },
        "far_cells_within_10px_of_footprint_edge": int((far_dist_edge <= 10).sum()),
        "candidates": candidates,
        "interpretation": (
            f"Every one of the {int((far_dist_edge <= 10).sum())} far cells lies within "
            f"{float(far_dist_edge.max()):.2f} px of the footprint boundary. A candidate with n dots passes only if "
            f"at least ceil(0.3*n) of them sit in those far cells; for the 22,163-dot candidate that is "
            f"{int(np.ceil((1 - OVERLAP_LIMIT) * 22163))} of {int(far.sum())} available cells, i.e. every one of them, "
            "on the study-area edge. No geologically motivated interior placement can satisfy the literal rule."
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    for c in candidates:
        print(f"{c['file'][-60:]}: overlap_vs_lattice={c['overlap_vs_lattice_3px']:.6f} "
              f"literal_pass={c['literal_lattice_gate_pass']} strict_format={c['validator_strict_local_format_pass']}")
    print("far cells:", out["footprint_cells_farther_than_3px_from_lattice"],
          "max distance to edge:", out["far_cells_min_distance_to_footprint_edge_px"]["max"])
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
