#!/usr/bin/env python3
"""Re-measure the nine focus-site submissions from their pinned GitHub commits.

What this does (no organizer access, no score claims):
  1. Downloads each pinned repository snapshot from codeload.github.com (tar.gz at the
     exact commit recorded in evidence/focus_sites_summary.json) and extracts the file.
  2. Checks SHA-256 against the recorded pin.
  3. Runs format checks against the official rules (EPSG 32611, 100 m, float32, one band,
     same shape/transform as the reference footprint, in-footprint finite values in [0,1],
     outside-footprint null/NaN OR masked) and reports whether outside cells are finite.
  4. Measures pairwise dot overlap (fraction of A's dots within 3 px of any B dot) and
     absolute rank correlation on a seeded footprint sample, for every pair.
  5. Measures proximity of each dot to the known catalogue (labels == 1), within 2 px.

Every number is a measurement on bytes. None is a leaderboard score; the user-reported
scores are copied, labelled, and never used as inputs to any metric.

Usage:  .venv/bin/python scripts/verify_focus_sites.py --cache /tmp/gems_focus_cache
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.io import MemoryFile
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

REPO = Path(__file__).resolve().parents[1]
SUMMARY = REPO / "evidence" / "focus_sites_summary.json"
REFERENCE = REPO / "data" / "bridge" / "labels.tif"  # labels footprint == sample footprint (checked)
OUT_JSON = REPO / "docs" / "data" / "focus-sites-verified.json"
OUT_CSV = REPO / "docs" / "data" / "focus-sites-verified.csv"
RADIUS_PX = 3.0
CATALOGUE_RADIUS_PX = 2.0
SAMPLE_N = 400_000
SEED = 20261030

URL_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+)/blob/([0-9a-f]{40})/(.+)$")


def _clean(obj):
    """Recursively replace non-finite floats with None so the JSON is strict."""
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_tarball(owner: str, repo: str, sha: str, cache: Path) -> Path:
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / f"{owner}__{repo}__{sha}.tar.gz"
    if not dest.exists() or dest.stat().st_size == 0:
        url = f"https://codeload.github.com/{owner}/{repo}/tar.gz/{sha}"
        tmp = dest.with_suffix(".partial")
        with urllib.request.urlopen(url, timeout=300) as resp, tmp.open("wb") as out:
            while True:
                block = resp.read(1 << 20)
                if not block:
                    break
                out.write(block)
        tmp.replace(dest)
    return dest


def extract_member(tarball: Path, inner_path: str) -> bytes:
    with tarfile.open(tarball, "r:gz") as tf:
        for member in tf.getmembers():
            # codeload tarballs put everything under "<repo>-<sha>/"
            if member.name.split("/", 1)[-1] == inner_path:
                handle = tf.extractfile(member)
                assert handle is not None
                return handle.read()
    raise FileNotFoundError(f"{inner_path} not found in {tarball.name}")


def dots_of(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    v = np.where(np.isfinite(values), values, 0.0)
    return footprint & (v > 0)


def format_checks(data: bytes, ref_shape, ref_transform, footprint: np.ndarray) -> dict:
    with MemoryFile(data) as mf, mf.open() as src:
        a = src.read(1).astype(np.float64)
        read_mask = src.read_masks(1) > 0
        checks = {
            "single_band": src.count == 1,
            "float32": src.dtypes[0] == "float32",
            "crs_epsg_32611": src.crs is not None and src.crs.to_epsg() == 32611,
            "res_100m": src.res == (100.0, 100.0),
            "shape_match": src.shape == ref_shape,
            "transform_match": tuple(src.transform)[:6] == tuple(ref_transform)[:6],
        }
        finite = np.isfinite(a)
        inside = footprint
        outside = ~footprint
        checks["inside_finite_all"] = bool(finite[inside].all())
        checks["inside_in_0_1"] = bool(((a >= 0) & (a <= 1))[inside & finite].all() and finite[inside].all())
        out_nan = int(np.count_nonzero(~finite & outside))
        out_finite = int(np.count_nonzero(finite & outside))
        checks["outside_null_or_nan_or_masked"] = bool(((~finite) | (~read_mask))[outside].all())
        # Reported-error guard: every raw cell (outside included) finite and in [0,1].
        checks["range_guard_whole_array_0_1"] = bool(finite.all() and ((a >= 0) & (a <= 1)).all())
        stats = {
            "nodata_tag": src.nodata,
            "outside_nan_count": out_nan,
            "outside_finite_count": out_finite,
            "outside_finite_values": sorted({float(x) for x in np.unique(a[outside & finite])[:5]}),
            "inside_nan_count": int(np.count_nonzero(~finite & inside)),
            "inside_min": float(np.nanmin(a[inside])) if finite[inside].any() else None,
            "inside_max": float(np.nanmax(a[inside])) if finite[inside].any() else None,
            "unique_inside_values": [float(x) for x in np.unique(a[inside & finite])[:6]],
        }
    return {"checks": checks, "stats": stats, "_array": a}


def pairwise_overlap(dots_a: np.ndarray, dots_b: np.ndarray, dist_b: np.ndarray) -> float:
    na = int(dots_a.sum())
    if na == 0:
        return float("nan")
    return float((dist_b[dots_a] <= RADIUS_PX).sum() / na)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cache", type=Path, default=Path("/tmp/gems_focus_cache"))
    ap.add_argument("--extra", type=Path, nargs="*", default=[],
                    help="additional local rasters to include (e.g. repo candidates)")
    args = ap.parse_args()

    summary = json.loads(SUMMARY.read_text())
    entries: list[dict] = []
    for s in summary["sites"]:
        m = URL_RE.match(s["artifact_url"])
        assert m, s["artifact_url"]
        owner, repo, sha, inner = m.group(1), m.group(2), m.group(3), m.group(4)
        entries.append({
            "label": s["site"], "kind": "focus-site-best", "owner": owner, "repo": repo,
            "commit": sha, "path": inner, "pinned_sha256": s["historic_best_sha256"],
            "user_reported_score": s["live_score"],
            "user_reported_label": "USER-REPORTED / UNVERIFIED; no organizer receipt",
        })
    for p in summary["our_candidates"].values():
        entries.append({"label": Path(p["file"]).name, "kind": "repo-candidate-local",
                        "local": REPO / p["file"], "pinned_sha256": p["sha256"]})
    for extra in args.extra:
        path = extra if extra.is_absolute() else REPO / extra
        entries.append({"label": path.name, "kind": "repo-candidate-local", "local": path,
                        "pinned_sha256": None})

    with rasterio.open(REFERENCE) as ref:
        ref_shape, ref_transform = ref.shape, ref.transform
        ref_valid = ref.read_masks(1) > 0
        labels = ref.read(1)
    footprint = ref_valid & np.isfinite(labels.astype(np.float64))
    known = footprint & (labels == 1)
    dist_known = distance_transform_edt(~known)

    rng = np.random.default_rng(SEED)
    fp_idx = np.flatnonzero(footprint.ravel())
    sample_idx = rng.choice(fp_idx, size=min(SAMPLE_N, fp_idx.size), replace=False)

    records = []
    dot_masks: dict[str, np.ndarray] = {}
    samples: dict[str, np.ndarray] = {}
    for e in entries:
        if e["kind"] == "focus-site-best":
            tb = fetch_tarball(e["owner"], e["repo"], e["commit"], args.cache)
            data = extract_member(tb, e["path"])
            e["source_url"] = f"https://github.com/{e['owner']}/{e['repo']}/blob/{e['commit']}/{e['path']}"
        else:
            data = Path(e["local"]).read_bytes()
            e["source_url"] = str(Path(e["local"]).relative_to(REPO))
        digest = sha256_bytes(data)
        fc = format_checks(data, ref_shape, ref_transform, footprint)
        a = fc.pop("_array")
        dmask = dots_of(a, footprint)
        dot_masks[e["label"]] = dmask
        samples[e["label"]] = np.where(np.isfinite(a), a, 0.0).ravel()[sample_idx]
        dots_in_known = int(np.count_nonzero(dmask & (dist_known <= CATALOGUE_RADIUS_PX)))
        records.append({
            "label": e["label"], "kind": e["kind"], "source_url": e["source_url"],
            "sha256": digest, "pinned_sha256": e["pinned_sha256"],
            "sha256_matches_pin": (digest == e["pinned_sha256"]) if e["pinned_sha256"] else None,
            "user_reported_score": e.get("user_reported_score"),
            "user_reported_label": e.get("user_reported_label"),
            "bytes": len(data), "dots": int(dmask.sum()),
            "dots_within_2px_of_catalogue": dots_in_known,
            "format_checks": fc["checks"], "format_stats": fc["stats"],
            "strict_official_pass": all(v for k, v in fc["checks"].items() if k != "range_guard_whole_array_0_1"),
            "range_guard_pass": fc["checks"]["range_guard_whole_array_0_1"],
        })
        print(f"{e['label']}: dots={int(dmask.sum())} sha_ok={digest == e['pinned_sha256']} "
              f"official_pass={all(fc['checks'].values())}", flush=True)

    labels_order = [r["label"] for r in records]
    pair: dict[str, dict] = {a: {} for a in labels_order}
    for b_lbl in labels_order:  # one distance transform in memory at a time
        dist_b = distance_transform_edt(~dot_masks[b_lbl]).astype(np.float32)
        for a_lbl in labels_order:
            if a_lbl == b_lbl:
                continue
            ov = pairwise_overlap(dot_masks[a_lbl], dot_masks[b_lbl], dist_b)
            rho = spearmanr(samples[a_lbl], samples[b_lbl]).statistic
            pair[a_lbl][b_lbl] = {"overlap_3px_of_A_dots": round(ov, 6), "abs_spearman": round(abs(float(rho)), 6)}
        del dist_b

    max_pairs = {}
    for a_lbl, row in pair.items():
        peer, best = max(row.items(), key=lambda kv: kv[1]["overlap_3px_of_A_dots"])
        max_pairs[a_lbl] = {"max_overlap_peer": peer, **best}
    for r in records:
        r["max_overlap_vs_any_other"] = max_pairs[r["label"]]

    out = {
        "schema": "focus-sites-verified-v1",
        "reference_footprint": "data/bridge/labels.tif valid mask (equals data/bridge/sample_submission.tif footprint; see IRREGULARITIES IR-S-06)",
        "footprint_cells": int(footprint.sum()),
        "catalogue_cells": int(known.sum()),
        "radius_px": RADIUS_PX, "catalogue_radius_px": CATALOGUE_RADIUS_PX,
        "sample": {"n": int(sample_idx.size), "seed": SEED},
        "gates": {"overlap_3px_max": 0.70, "abs_spearman_max": 0.90},
        "scores_label": "USER-REPORTED / UNVERIFIED (copied from the prompt; not measured here)",
        "records": records,
        "pairwise": pair,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(_clean(out), indent=2, allow_nan=False) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["label", "kind", "dots", "sha256_matches_pin", "official_format_pass", "range_guard_pass",
                    "outside_finite_count", "user_reported_score", "max_overlap_peer",
                    "max_overlap_3px", "max_abs_spearman", "sha256"])
        for r in records:
            m = r["max_overlap_vs_any_other"]
            w.writerow([r["label"], r["kind"], r["dots"], r["sha256_matches_pin"],
                        r["strict_official_pass"], r["range_guard_pass"], r["format_stats"]["outside_finite_count"],
                        r["user_reported_score"], m["max_overlap_peer"],
                        m["overlap_3px_of_A_dots"], m["abs_spearman"], r["sha256"]])
    print(f"wrote {OUT_JSON.relative_to(REPO)} and {OUT_CSV.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
