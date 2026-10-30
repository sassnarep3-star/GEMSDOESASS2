#!/usr/bin/env python3
"""Uniqueness gate for a candidate submission raster against the rebuilt GEMSDOE registry.

Protocol (project parallel-run rules, LANE clause):
  * forward 3-px overlap = fraction of the candidate's dots within 3 px of a registry raster's dots.
    FAIL if > 0.70 against any eligible registry raster.
  * absolute Spearman rho over the template footprint (fixed 200,000-cell sample, seed 20261030).
    FAIL if > 0.90 against any eligible registry raster.
  * exact duplicate: identical positive-pixel set (IoU = 1) or identical file SHA-256 -> FAIL.
  * registry: registry/gems_registry_manifest.json entries with eligible_template_grid = true.
    Blobs are read from the local cache (rebuilt by scripts/build_gems_registry.py) and their
    git SHA-1 was verified at download time.

Usage: python scripts/gate_candidate.py <candidate.tif> <evidence_out.json> [--label NAME]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "gems_registry_manifest.json"
CACHE = Path(os.environ.get("GEMS_REGISTRY", str(Path.home() / ".cache" / "registry")))
BLOBS = CACHE / "blobs"
RADIUS = 3.0
OVERLAP_MAX = 0.70
RHO_MAX = 0.90
SAMPLE = 200_000
TEMPLATE = ROOT / "data" / "bridge" / "sample_submission.tif"


def positives(a: np.ndarray) -> np.ndarray:
    return np.isfinite(a) & (a > 0.5)


def fraction_within(src_pts: np.ndarray, ref_pts: np.ndarray, shape) -> float:
    if len(src_pts) == 0:
        return 0.0
    if len(ref_pts) == 0:
        return 0.0
    if len(ref_pts) <= 300_000:
        d, _ = cKDTree(ref_pts).query(src_pts, k=1)
        return float((d <= RADIUS).mean())
    mask = np.zeros(shape, dtype=bool)
    mask[ref_pts[:, 0], ref_pts[:, 1]] = True
    d = distance_transform_edt(~mask)
    return float((d[src_pts[:, 0], src_pts[:, 1]] <= RADIUS).mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("out")
    ap.add_argument("--label", default=None)
    ap.add_argument("--exclude-self", action="store_true",
                    help="for a file already in the registry: skip its own bytes (sha256) when comparing")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    entries = [e for e in manifest["entries"] if e.get("eligible_template_grid") and e.get("blob")]
    with rasterio.open(args.candidate) as ds:
        cand = ds.read(1)
        cand_meta = {"shape": list(ds.shape), "crs": ds.crs.to_string(), "dtype": str(ds.dtypes[0]),
                     "transform": list(ds.transform)[:6], "nodata": ds.nodata, "count": ds.count}
    cand_pos = positives(cand)
    cand_pts = np.argwhere(cand_pos)
    cand_bytes = Path(args.candidate).read_bytes()
    cand_sha = hashlib.sha256(cand_bytes).hexdigest()
    with rasterio.open(TEMPLATE) as ds:
        foot = np.isfinite(ds.read(1))
    foot_idx = np.flatnonzero(foot.ravel())
    rng = np.random.default_rng(20261030)
    sample_idx = rng.choice(foot_idx, size=min(SAMPLE, foot_idx.size), replace=False)
    cand_s = cand.ravel()[sample_idx].astype(np.float64)

    seen_blobs: set[str] = set()
    rows = []
    missing = []
    for e in entries:
        if e["blob"] in seen_blobs:
            continue
        seen_blobs.add(e["blob"])
        if args.exclude_self and e.get("sha256") == cand_sha:
            continue
        path = BLOBS / f"{e['blob']}.tif"
        if not path.exists():
            missing.append(e["blob"])
            continue
        with rasterio.open(path) as ds:
            ref = ds.read(1)
        ref_pos = positives(ref)
        ref_pts = np.argwhere(ref_pos)
        fwd = fraction_within(cand_pts, ref_pts, cand.shape)
        rev = fraction_within(ref_pts, cand_pts, cand.shape) if len(ref_pts) else 0.0
        ref_s = ref.ravel()[sample_idx].astype(np.float64)
        ok = np.isfinite(ref_s)
        rho = float(spearmanr(cand_s[ok], ref_s[ok]).statistic) if ok.sum() > 2 and np.ptp(ref_s[ok]) > 0 and np.ptp(cand_s[ok]) > 0 else 0.0
        iou_exact = bool(np.array_equal(cand_pos, ref_pos))
        rows.append({
            "repo": e["repo"], "path": e["path"], "blob": e["blob"], "sha256": e.get("sha256"),
            "n_positive": int(ref_pos.sum()), "overlap_3px_fwd": round(fwd, 6), "overlap_3px_rev": round(rev, 6),
            "abs_spearman": round(abs(rho), 6), "identical_positive_set": iou_exact,
        })

    worst_fwd = max(rows, key=lambda r: r["overlap_3px_fwd"]) if rows else None
    worst_rho = max(rows, key=lambda r: r["abs_spearman"]) if rows else None
    exact = [r for r in rows if r["identical_positive_set"] or r["sha256"] == cand_sha]
    fails = []
    if worst_fwd and worst_fwd["overlap_3px_fwd"] > OVERLAP_MAX:
        fails.append("overlap_3px")
    if worst_rho and worst_rho["abs_spearman"] > RHO_MAX:
        fails.append("spearman")
    if exact:
        fails.append("exact_duplicate")
    verdict = "PASS (lane gate)" if not fails else "FAIL: " + ",".join(fails)

    out = {
        "label": args.label or Path(args.candidate).name,
        "candidate_file": Path(args.candidate).name,
        "candidate_sha256": cand_sha,
        "candidate_format": cand_meta,
        "candidate_dots": int(cand_pos.sum()),
        "gate": {"overlap_3px_max": OVERLAP_MAX, "abs_spearman_max": RHO_MAX, "radius_px": RADIUS},
        "registry_manifest": str(MANIFEST.relative_to(ROOT)),
        "registry_manifest_generated_utc": manifest.get("generated_utc"),
        "exclude_self": bool(args.exclude_self),
        "registry_unique_eligible_rasters_compared": len(rows),
        "registry_blobs_missing_from_cache": missing,
        "worst_overlap_3px_fwd": worst_fwd,
        "worst_abs_spearman": worst_rho,
        "exact_duplicates": exact,
        "verdict": verdict,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "closest_by_overlap": sorted(rows, key=lambda r: -r["overlap_3px_fwd"])[:10],
        "all_rows": rows,
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"{out['label']}: dots={out['candidate_dots']} compared={len(rows)} "
          f"max_fwd_overlap={worst_fwd['overlap_3px_fwd'] if worst_fwd else None} "
          f"max_abs_rho={worst_rho['abs_spearman'] if worst_rho else None} verdict={verdict} "
          f"missing={len(missing)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
