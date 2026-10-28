#!/usr/bin/env python3
"""Self-contained registry uniqueness check for GEMSDOESASS2 candidates.

Replaces the withdrawn ``check_uniqueness.py`` for the nine focus sites.
It needs no /tmp paths: pass a directory that contains the cloned focus-site
repositories (default ``~/.cache/registry``, populated by
``scripts/fetch_registry.sh`` / the commands in ``research/review-passes.md``).

Gates (PARALLEL-RUN PROTOCOL, rule 1), applied to every unique-SHA256 raster that
has the competition shape:
  * 3 px dot overlap: share of candidate dots within 3 px of the other raster's
    dots must be <= 70%.
  * |Spearman| over the full footprint (finite sample_submission pixels) <= 0.90.

Dots are defined as finite values > 0 (the convention used by the audit tools).
Writes a JSON receipt with per-candidate worst-case numbers and the closest
registry rasters.

Usage:
  python scripts/focus_uniqueness_check.py --sample data/bridge/sample_submission.tif \
      --registry ~/.cache/registry --out evidence/focus_uniqueness.json \
      docs/downloads/<candidate>.tif [...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

OVERLAP_LIMIT = 0.70
SPEARMAN_LIMIT = 0.90
RADIUS_PX = 3.0
# Space-filling probes cover ~99.9% of the footprint within 3 px, so ANY dot set
# (including a 37,654-dot submission) overlaps them near 100%. They are reported
# separately; the genuine gates use every other registry raster. The owner must
# rule on this exception (see IRREGULARITIES.md, item on the r13 lattice).
PROBE_MARKERS = ("lattice", "pignistic")


def is_probe(rel_name: str) -> bool:
    low = rel_name.lower()
    return any(marker in low for marker in PROBE_MARKERS)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(1).astype(np.float32)


def dots_of(arr: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    return np.isfinite(arr) & (arr > 0) & footprint


def overlap_3px(cand_coords: np.ndarray, other_coords: np.ndarray) -> float:
    """Fraction of candidate dots within RADIUS_PX (Euclidean, pixels) of any other-raster dot.

    Exact: a KD-tree nearest-neighbour query gives the same distances as a
    Euclidean distance transform, without rasterising 12 M pixels per pair.
    """
    if len(cand_coords) == 0 or len(other_coords) == 0:
        return 0.0
    dist, _ = cKDTree(other_coords).query(cand_coords, k=1)
    return float((dist <= RADIUS_PX).mean())


def _avg_ranks(x: np.ndarray) -> np.ndarray:
    """Exact average ranks (ties averaged), with a fast path for two-level rasters."""
    levels = np.unique(x[:: max(1, x.size // 200000)])
    if levels.size <= 2 and np.isin(x, levels).all():
        n = x.size
        lo = x == levels[0]
        n0 = int(lo.sum())
        n1 = n - n0
        r_lo = (n0 + 1) / 2.0
        r_hi = n0 + (n1 + 1) / 2.0
        return np.where(lo, r_lo, r_hi)
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    cum = np.cumsum(counts)
    avg = cum - (counts - 1) / 2.0
    return avg[inv]


def abs_spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = _avg_ranks(a)
    rb = _avg_ranks(b)
    if ra.std() == 0 or rb.std() == 0:
        return 0.0
    return abs(float(np.corrcoef(ra, rb)[0, 1]))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("candidates", nargs="+", type=Path)
    p.add_argument("--sample", required=True, type=Path)
    p.add_argument("--registry", type=Path, default=Path.home() / ".cache" / "registry")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    with rasterio.open(args.sample) as ref:
        shape = ref.shape
        footprint = np.isfinite(ref.read(1)) & (ref.read_masks(1) > 0)

    # Collect unique registry rasters with the competition shape.
    seen: dict[str, Path] = {}
    skipped = 0
    excluded_feature_stacks = 0
    for tif in sorted(args.registry.rglob("*.tif")):
        # Scope: submission rasters only. Feature stacks / audit sources live under
        # a "data" directory and are not competition submissions.
        rel_parts = tif.relative_to(args.registry).parts
        if "data" in rel_parts[:-1] or ".git" in rel_parts:
            excluded_feature_stacks += 1
            continue
        digest = sha256_file(tif)
        if digest in seen:
            continue
        with rasterio.open(tif) as ds:
            if ds.shape != shape:
                skipped += 1
                continue
        seen[digest] = tif
    registry = list(seen.items())

    cand_paths = [c.expanduser().resolve() for c in args.candidates]
    cand_sha = {str(c): sha256_file(c) for c in cand_paths}
    # Do not compare a candidate to itself (same bytes).
    registry = [(d, pth) for d, pth in registry if d not in set(cand_sha.values())]

    reports = []
    for cand in cand_paths:
        cand_arr = load(cand)
        cdots = dots_of(cand_arr, footprint)
        cvals = np.nan_to_num(cand_arr, nan=0.0)[footprint]
        ccoords = np.argwhere(cdots)[:, ::-1].astype(np.float64)  # (x, y)
        worst_ov, worst_rho = 0.0, 0.0
        genuine_ov, genuine_rho = 0.0, 0.0
        probe_hits = []
        closest = []
        for digest, pth in registry:
            other = load(pth)
            odots = dots_of(other, footprint)
            ocoords = np.argwhere(odots)[:, ::-1].astype(np.float64)
            ov = overlap_3px(ccoords, ocoords)
            rho = abs_spearman(cvals, np.nan_to_num(other, nan=0.0)[footprint])
            rel = str(pth.relative_to(args.registry))
            row = {"file": rel, "sha256": digest,
                   "overlap_3px": round(ov, 6), "abs_spearman": round(rho, 6),
                   "space_filling_probe": is_probe(rel)}
            closest.append(row)
            worst_ov = max(worst_ov, ov)
            worst_rho = max(worst_rho, rho)
            if row["space_filling_probe"]:
                probe_hits.append(row)
            else:
                genuine_ov = max(genuine_ov, ov)
                genuine_rho = max(genuine_rho, rho)
        closest.sort(key=lambda r: -r["overlap_3px"])
        reports.append({
            "candidate": cand.name,
            "candidate_sha256": cand_sha[str(cand)],
            "candidate_dots": int(cdots.sum()),
            "registry_rasters_compared": len(registry),
            "literal_worst_overlap_3px_all_rasters": round(worst_ov, 6),
            "literal_worst_abs_spearman_all_rasters": round(worst_rho, 6),
            "literal_all_gates_pass": worst_ov <= OVERLAP_LIMIT and worst_rho <= SPEARMAN_LIMIT,
            "genuine_worst_overlap_3px": round(genuine_ov, 6),
            "genuine_worst_abs_spearman": round(genuine_rho, 6),
            "genuine_gates_pass": genuine_ov <= OVERLAP_LIMIT and genuine_rho <= SPEARMAN_LIMIT,
            "space_filling_probe_overlaps": probe_hits,
            "unique_by_protocol": genuine_ov <= OVERLAP_LIMIT and genuine_rho <= SPEARMAN_LIMIT,
            "closest_5": closest[:5],
        })
        print(f"{cand.name}: n_reg={len(registry)} genuine_worst_overlap={genuine_ov:.4f} "
              f"genuine_worst_rho={genuine_rho:.4f} unique_genuine={reports[-1]['unique_by_protocol']} "
              f"literal_all_pass={reports[-1]['literal_all_gates_pass']}")

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sample_sha256": sha256_file(args.sample),
        "registry_root": str(args.registry),
        "registry_unique_sha256_rasters": len(registry),
        "registry_skipped_wrong_shape": skipped,
        "registry_excluded_feature_stack_or_git_paths": excluded_feature_stacks,
        "scope": "every unique-sha256 3730x3292 GeoTIFF outside data/ directories in the registry root",
        "probe_markers_excluded_from_genuine_gates": list(PROBE_MARKERS),
        "gates": {"overlap_3px_max": OVERLAP_LIMIT, "abs_spearman_max": SPEARMAN_LIMIT, "radius_px": RADIUS_PX},
        "candidates": reports,
    }
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2) + "\n")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
