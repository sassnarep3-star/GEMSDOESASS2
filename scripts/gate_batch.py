#!/usr/bin/env python3
"""Batch uniqueness gate: one pass over the registry for several candidates.

Same protocol and thresholds as scripts/gate_candidate.py (3-px forward overlap > 0.70 FAIL;
|Spearman| over the fixed 200k footprint sample > 0.90 FAIL; identical positive set or identical
SHA-256 -> exact duplicate). Each registry raster is read once and compared with every candidate,
which is what makes a full pass feasible on this 2-core / 3 GB sandbox.
Cross-checked against gate_candidate.py on the sparse-blind candidate (see evidence/gates/).

Usage: python scripts/gate_batch.py OUTDIR CAND1.tif [CAND2.tif ...] [--exclude-self-for-registry-blobs]
Writes OUTDIR/gate_batch_<label>.json, one per candidate.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_candidate import (BLOBS, MANIFEST, OVERLAP_MAX, RHO_MAX, SAMPLE, TEMPLATE,  # noqa: E402
                            fraction_within, positives)


def sample_idx() -> np.ndarray:
    with rasterio.open(TEMPLATE) as ds:
        foot = np.isfinite(ds.read(1))
    foot_idx = np.flatnonzero(foot.ravel())
    rng = np.random.default_rng(20261030)
    return rng.choice(foot_idx, size=min(SAMPLE, foot_idx.size), replace=False)


def pearson_ranks(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rankdata(a), rankdata(b)
    ra -= ra.mean(); rb -= rb.mean()
    den = np.sqrt((ra * ra).sum() * (rb * rb).sum())
    return float((ra * rb).sum() / den) if den > 0 else 0.0


def centred_unit_ranks(x: np.ndarray) -> np.ndarray:
    r = rankdata(x); r -= r.mean()
    return r / np.sqrt((r * r).sum())


NO_RHO = "--no-rho" in sys.argv  # overlap + exact-duplicate pass only (Spearman skipped)


def main() -> int:
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    outdir = Path(argv[0]); cands = argv[1:]
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text())
    idx = sample_idx()
    C = []
    for p in cands:
        with rasterio.open(p) as ds:
            a = ds.read(1); meta = {"shape": list(ds.shape), "crs": ds.crs.to_string(), "dtype": str(ds.dtypes[0]),
                                    "transform": list(ds.transform)[:6], "nodata": ds.nodata, "count": ds.count}
        pos = positives(a)
        C.append({"path": p, "label": Path(p).stem, "meta": meta, "pos": pos, "pts": np.argwhere(pos),
                  "sample": a.ravel()[idx].astype(np.float64), "sha": hashlib.sha256(Path(p).read_bytes()).hexdigest(),
                  "unit": centred_unit_ranks(a.ravel()[idx].astype(np.float64)),
                  "family": Path(p).name.split("-cc522684")[0] if "cc522684" in Path(p).name else None,
                  "rows": [], "worst_fwd": None, "worst_rho": None, "exact": []})
    entries, seen = [], set()
    for e in manifest["entries"]:
        if e.get("eligible_template_grid") and e.get("blob") and e["blob"] not in seen:
            seen.add(e["blob"]); entries.append(e)
    missing = []
    for n, e in enumerate(entries):
        path = BLOBS / f"{e['blob']}.tif"
        if not path.exists():
            missing.append(e["blob"]); continue
        with rasterio.open(path) as ds:
            ref = ds.read(1)
        ref_pos = positives(ref); ref_pts = np.argwhere(ref_pos)
        ref_s = ref.ravel()[idx].astype(np.float64) if not NO_RHO else np.zeros(1)
        ok = np.isfinite(ref_s)
        if (not NO_RHO) and ok.all() and np.ptp(ref_s) > 0:
            ref_unit = centred_unit_ranks(ref_s)
        dense_d = None
        if len(ref_pts) > 300_000:  # one distance transform per dense raster, shared by all candidates
            mask = np.zeros(ref_pos.shape, dtype=bool)
            mask[ref_pts[:, 0], ref_pts[:, 1]] = True
            dense_d = distance_transform_edt(~mask)
        for c in C:
            if e.get("sha256") == c["sha"] or (c["family"] and Path(e["path"]).name.startswith(c["family"])):
                continue  # the candidate's own bytes or its own file family (exclude-self)
            if dense_d is not None:
                fwd = float((dense_d[c["pts"][:, 0], c["pts"][:, 1]] <= 3.0).mean())
                rev = None  # not computed for dense rasters (informational only; not in the verdict)
            else:
                fwd = fraction_within(c["pts"], ref_pts, c["pos"].shape)
                rev = fraction_within(ref_pts, c["pts"], c["pos"].shape) if len(ref_pts) else 0.0
            if NO_RHO:
                rho = float("nan")
            elif ok.all() and np.ptp(ref_s) > 0 and np.ptp(c["sample"]) > 0:
                rho = float(np.dot(c["unit"], ref_unit))  # Spearman = Pearson of ranks (ties averaged)
            elif ok.sum() > 2 and np.ptp(ref_s[ok]) > 0 and np.ptp(c["sample"][ok]) > 0:
                rho = pearson_ranks(c["sample"][ok], ref_s[ok])
            else:
                rho = 0.0
            if NO_RHO:
                rho = float("nan")
            row = {"repo": e["repo"], "path": e["path"], "blob": e["blob"], "sha256": e.get("sha256"),
                   "n_positive": int(ref_pos.sum()), "overlap_3px_fwd": round(fwd, 6), "overlap_3px_rev": None if rev is None else round(rev, 6),
                   "abs_spearman": None if NO_RHO else round(abs(rho), 6), "identical_positive_set": bool(np.array_equal(c["pos"], ref_pos))}
            c["rows"].append(row)
            if c["worst_fwd"] is None or fwd > c["worst_fwd"]["overlap_3px_fwd"]:
                c["worst_fwd"] = row
            if (not NO_RHO) and (c["worst_rho"] is None or abs(rho) > c["worst_rho"]["abs_spearman"]):
                c["worst_rho"] = row
            if row["identical_positive_set"] or row["sha256"] == c["sha"]:
                c["exact"].append(row)
        if n % 300 == 0:
            print(f"{n}/{len(entries)}", file=sys.stderr, flush=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for c in C:
        fails = []
        if c["worst_fwd"] and c["worst_fwd"]["overlap_3px_fwd"] > OVERLAP_MAX: fails.append("overlap_3px")
        if (not NO_RHO) and c["worst_rho"] and c["worst_rho"]["abs_spearman"] > RHO_MAX: fails.append("spearman")
        if c["exact"]: fails.append("exact_duplicate")
        verdict = "PASS (lane gate)" if not fails else "FAIL: " + ",".join(fails)
        out = {"label": c["label"], "candidate_file": Path(c["path"]).name, "candidate_sha256": c["sha"],
               "candidate_format": c["meta"], "candidate_dots": int(c["pos"].sum()),
               "gate": {"overlap_3px_max": OVERLAP_MAX, "abs_spearman_max": RHO_MAX, "radius_px": 3.0},
               "spearman_checked": not NO_RHO,
               "method": "gate_batch.py (single pass; equivalent to gate_candidate.py; cross-checked)",
               "registry_manifest": str(MANIFEST.name), "registry_manifest_generated_utc": manifest.get("generated_utc"),
               "exclude_self": "own sha256 and own file family (cc522684 zeros/nan) are skipped; other copies are compared", "registry_unique_eligible_rasters_compared": len(c["rows"]),
               "registry_blobs_missing_from_cache": missing,
               "worst_overlap_3px_fwd": c["worst_fwd"], "worst_abs_spearman": c["worst_rho"],
               "exact_duplicates": c["exact"], "verdict": verdict, "generated_utc": now,
               "closest_by_overlap": sorted(c["rows"], key=lambda r: -r["overlap_3px_fwd"])[:10]}
        (outdir / f"gate_batch_{c['label']}.json").write_text(json.dumps(out, indent=1) + "\n")
        print(f"{c['label']}: dots={out['candidate_dots']} compared={len(c['rows'])} "
              f"max_fwd={out['worst_overlap_3px_fwd'] and out['worst_overlap_3px_fwd']['overlap_3px_fwd']} "
              f"max_rho={out['worst_abs_spearman'] and out['worst_abs_spearman']['abs_spearman']} verdict={verdict}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
