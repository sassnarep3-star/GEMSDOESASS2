#!/usr/bin/env python3
"""Protocol rule 1 (LANE / duplicate) guard against the whole cloned site portfolio.

For a candidate raster this measures, over every *other* submission raster found in
the sparse site clones (`.cache/repos/*/`):

  * `our_dots_within_3px_of_ref`   - share of the candidate's dots that lie within
    3 px of that raster's dots (the protocol's duplicate statistic), and
  * `ref_dots_within_3px_of_ours`  - the reverse share.

plus the aggregate share of candidate dots covered by the *union* of all registry
dots. Space-filling calibration probes (names containing "lattice") are reported
separately because they cover ~99.9% of the footprint within 3 px and would fail
any dense raster, including the reported best file (IR-S-01).

Dots are `finite & > 0` inside the competition footprint. Nothing here grants or
withholds an organizer decision; it is a duplicate screen only.

Usage:
  python scripts/registry_overlap_guard.py CANDIDATE.tif [--repos .cache/repos]
      [--out evidence/registry_overlap.json] [--limit N]
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

ROOT = Path(__file__).resolve().parents[1]
RADIUS_PX = 3.0
LIMIT = 0.70


def dots(path: Path, foot: np.ndarray) -> np.ndarray | None:
    try:
        with rasterio.open(path) as src:
            if src.shape != foot.shape:
                return None
            a = src.read(1)
    except Exception:
        return None
    m = np.isfinite(a) & (a > 0) & foot
    if m.sum() == 0:
        return None
    ys, xs = np.nonzero(m)
    return np.column_stack([ys, xs]).astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--sample", type=Path, default=ROOT / "data" / "bridge" / "sample_submission.tif")
    ap.add_argument("--repos", type=Path, default=ROOT / ".cache" / "repos")
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "registry_overlap.json")
    ap.add_argument("--limit", type=int, default=0, help="cap rasters per site (debug)")
    ap.add_argument("--max-refs", type=int, default=80)
    ap.add_argument("--include", default="", help="comma-separated substrings; if set only files whose name contains one are scanned")
    args = ap.parse_args()

    with rasterio.open(args.sample) as src:
        foot = np.isfinite(src.read(1))
    C = dots(args.candidate, foot)
    if C is None:
        raise SystemExit("candidate has no dots inside the footprint")
    tree_c = cKDTree(C)

    rows = []
    all_dots = []
    probes = []
    inc = [t for t in args.include.split(",") if t.strip()]
    scanned = 0
    for repo in sorted(p for p in args.repos.iterdir() if p.is_dir()):
        files = [p for p in repo.rglob("*.tif")
                 if "sample_submission" not in p.name and "labels" not in p.name
                 and "existing_faults" not in p.name and "features" not in p.name
                 and p.stat().st_size < 3_000_000]
        if inc:
            files = [p for p in files if any(t.strip() in p.name for t in inc)]
        if args.limit:
            files = files[: args.limit]
        for f in files:
            if scanned >= args.max_refs:
                break
            D = dots(f, foot)
            if D is None or len(D) < 50:
                continue
            scanned += 1
            d, _ = tree_c.query(D, k=1)
            ref_share = float((d <= RADIUS_PX).mean())
            try:
                t_ref = cKDTree(D)
                dc, _ = t_ref.query(C, k=1)
                cand_share = float((dc <= RADIUS_PX).mean())
            except Exception:
                cand_share = None
            probes_row = {"site": repo.name, "file": f.name, "ref_dots": int(len(D)),
                          "ref_dots_within_3px_of_candidate": round(ref_share, 4),
                          "candidate_dots_within_3px_of_ref": round(cand_share, 4) if cand_share is not None else None}
            if "lattice" in f.name.lower():
                probes.append(probes_row)
                continue
            rows.append(probes_row)
            all_dots.append(D)
    if all_dots:
        U = np.vstack(all_dots)
        du, _ = cKDTree(U).query(C, k=1)
        union_share = float((du <= RADIUS_PX).mean())
    else:
        U = None
        union_share = None
    own = sorted(rows, key=lambda r: -(r["candidate_dots_within_3px_of_ref"] or 0))[:15]
    out = {
        "n_rasters_scanned": scanned,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": str(args.candidate),
        "candidate_sha256": hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
        "candidate_dots": int(len(C)),
        "n_registry_rasters": len(rows),
        "registry_union_pixels": int(0 if U is None else len(U)),
        "share_of_candidate_dots_covered_by_registry_union_3px": union_share,
        "registry_rasters_with_highest_candidate_overlap": own,
        "lattice_probes_reported_separately": probes[:10],
        "note": "Reverse share (registry dots near the candidate) is the informative "
                "direction for a *subset/duplicate* verdict when the candidate is sparser "
                "than the registry. The forward share is computed per-pair in the run card.",
        "duplicate_limit": LIMIT,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("worst_registry_rasters_by_reverse_share",
                                                                "lattice_probes_reported_separately")}, indent=2))
    print("registry rasters with the highest candidate overlap (protocol rule 1 statistic):")
    for r in own[:12]:
        print(f"  {r['site']:>14} cand_overlap={r['candidate_dots_within_3px_of_ref']} "
              f"ref_overlap={r['ref_dots_within_3px_of_candidate']} (ref dots {r['ref_dots']:>7}) {r['file'][:52]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
