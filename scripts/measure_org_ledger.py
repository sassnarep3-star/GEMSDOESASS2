#!/usr/bin/env python3
"""Measure geometric properties of organizer-scored submission rasters across the
GEMSDOE site portfolio, to build an empirical score-vs-geometry ledger.

Every row pairs (a) a raster downloaded from the site's own repository mirror and
matched by name to a score the owner reported on that site's page, with (b)
properties measured here from the bytes: dot count, value statistics, distance to
the public fault catalogue, and how much of the emission sits inside the 3 px
(false-positive-free) tolerance halo of a mapped fault.

The scores are USER-REPORTED / UNVERIFIED: no organizer receipt ties a score to
these bytes. Nothing here is a holdout score or a leaderboard projection.

Usage:
  python scripts/measure_org_ledger.py --out evidence/org_ledger_measured.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "data" / "bridge" / "labels.tif"
SAMPLE = ROOT / "data" / "bridge" / "sample_submission.tif"
CACHE = ROOT / ".cache" / "ledger"  # sibling: .cache/repos holds the sparse clones

# (site, owner repo, name stem as printed on the site page, owner-reported score)
LEDGER = [
    ("GEMSDOE24", "buffedlizard55-lab/GEMSDOE24", "h25-1-dotted-h19-5-d1-5-20261002-989f59505db1", 0.2477),
    ("GEMSDOE25", "buffedlizard55-lab/GEMSDOE25", "dotted-h19-5-d2-8-20261002-e56ea318af89", 0.2600),
    ("GEMSDOE27", "buffedlizard55-lab/GEMSDOE27", "topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1", 0.2449),
    ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc", 0.2708),
    ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e", 0.2649),
    ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "h36-1-rung30-blind-r1-20261003-b531dae0a36f", 0.2710),
    ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "h38-1-hf-euler-r30-r1-20261003-56a9f473edc7", 0.2707),
    ("GEMSDOE30", "buffedlizard55-lab/GEMSDOE30", "d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600),
    ("GEMSDOE31", "buffedlizard55-lab/GEMSDOE31", "h27-4-solo-d28-20261004-8acb75e1", 0.2708),
    ("GEMSDOE32", "buffedlizard55-lab/GEMSDOE32", "h33-h33-2-b2-20261004T220000Z-e5eb6e7e", 0.2778),
    ("GEMSDOE33", "buffedlizard55-lab/GEMSDOE33", "h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632),
    ("GEMSDOE36", "buffedlizard55-lab/GEMSDOE36", "anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6", 0.2750),
    ("19GEMSDOE", "buffedlizard55-lab/19GEMSDOE", "h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa", 0.1894),
    ("19GEMSDOE", "buffedlizard55-lab/19GEMSDOE", "h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf", 0.1922),
    ("GEMSDOE10", "buffedlizard55-lab/GEMSDOE10", "h28-dotted-ridge-20260928T020256236880Z-6452ae1d00", 0.1839),
    ("GEMSDOE10", "buffedlizard55-lab/GEMSDOE10", "H25-ctx-ridge-20260927T232947704150Z-6452ae1d00", 0.1280),
    ("13GEMSDOE", "buffedlizard55-lab/13GEMSDOE", "r13-lattice-s5_v2", 0.0904),
    ("16GEMSDOE", "buffedlizard55-lab/16GEMSDOE", "h16-1-topo-geophys-baseline-ridges-20260930-df20f65e", 0.1855),
    ("20GEMSDOE", "buffedlizard55-lab/20GEMSDOE", "h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b", 0.1890),
    ("GEMSDOE29", "buffedlizard55-lab/GEMSDOE29", "efd28-repro-20261003-1cc7dc534d51", 0.2600),
    ("GEMSDOE29", "buffedlizard55-lab/GEMSDOE29", "wormrank-d28-20261003-59dcaf6dd11d", 0.2560),
    ("GEMSDOE29", "buffedlizard55-lab/GEMSDOE29", "sgmc-off-catalogue-44k-20261003-c8dcd780e3fd", 0.0512),
    ("GEMSDOE29", "buffedlizard55-lab/GEMSDOE29", "repo-c0-habitat-emission-20261003-a4d439b07426", 0.0041),
    ("GEMSDOE23", "buffedlizard55-lab/GEMSDOE23", "h30-arrangement-matched-habitat-20261002-0d4e02e8", 0.1352),
    ("GEMSDOE49", "buffedlizard55-lab/GEMSDOE49", "gate_ortho_w0.25-40k-20261006T213721Z", 0.2376),
    ("GEMSDOE63", "buffedlizard55-lab/GEMSDOE63", "cvarlw-thin-s3p17-54864-20261011T220606Z-c58f60c4", 0.2303),
    ("GEMSDOE48", "buffedlizard55-lab/GEMSDOE48", "h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8", 0.2296),
    ("GEMSDOE70", "buffedlizard55-lab/GEMSDOE70", "gems70-p5-dual-submod300-oof38k-20261020", 0.2478),
    ("GEMSDOE76", "buffedlizard55-lab/GEMSDOE76", "gems76-ptcf-tiltworm-submod39k-20261021T034000Z-6316481d", 0.2343),
    ("GEMSDOE76", "buffedlizard55-lab/GEMSDOE76", "gems76_h76_3_geotherm_tilt_axial_submod_20261021_zeros", 0.1555),
    ("GEMSDOE73", "buffedlizard55-lab/GEMSDOE73", "gems73-h73-mcsc-seamfree-blakely-37654dots-20261021T073716Z-b27ac445", 0.1917),
    ("GEMSDOE82", "buffedlizard55-lab/GEMSDOE82", "gemsdoe82-h82-submodular-punoisyor-20261021T235456Z-fe137199", 0.1886),
    ("GEMSDOE21", "buffedlizard55-lab/GEMSDOE21", "h19-4-reference-20260930-691e4dfa", 0.1894),
    ("7GEMSDOE", "buffedlizard55-lab/7GEMSDOE", "lidarscarp-ridge-top2pct", 0.1461),
    ("12GEMSDOE", "buffedlizard55-lab/12GEMSDOE", "r7-nms3-dem10-scarp", 0.1294),
    ("GEMSDOE75", "buffedlizard55-lab/GEMSDOE75", "gems75-trlt-radon-loco-ridge-20261021", 0.1627),
    ("GEMSDOE78", "buffedlizard55-lab/GEMSDOE78", "gems78-h78sigx-fuse-b5-44090dots-20261022T021932Z-zeros", 0.1564),
    ("GEMSDOE2", "buffedlizard55-lab/GEMSDOE2", "gemsdoe2-dual-family-union-20260925T160406Z-f68e590f", 0.1560),
    ("GEMSDOE", "buffedlizard55-lab/GEMSDOE", "gems-submission-20260925T001403Z-7f00890a", 0.1563),
    ("GEMSDOE91", "buffedlizard55-lab/GEMSDOE91", "gems91-s17-lftg-20261025T160014Z-7b6bf90844", 0.1823),
    ("GEMSDOE67", "buffedlizard55-lab/GEMSDOE67", "ovtr-ml-cover-tau3p0-20261012", 0.1426),
]


def gh(*args: str) -> str:
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=120)
    if r.returncode:
        raise RuntimeError(r.stderr.strip()[:200])
    return r.stdout


def gh_raw(repo: str, path: str, ref: str) -> bytes:
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H",
         "Accept: application/vnd.github.raw+json"],
        capture_output=True, timeout=300)
    if r.returncode:
        raise RuntimeError(r.stderr.decode()[:200])
    return r.stdout


def find_raster(site: str, stem: str) -> tuple[str, str, int] | None:
    """Return (path, sha256, size) of the smallest locally-cloned raster whose file
    name contains every token of the stem (matches -nan/-zeros/-allfinite variants;
    the smallest variant is preferred so that we measure the emission, not a stack).

    Reads the sparse clones produced by scripts/clone_site_portfolios.sh, i.e. the
    site's own committed bytes. No network calls, no GitHub API quota used."""
    root = CACHE.parent / "repos" / site
    if not root.is_dir():
        return None
    toks = [t for t in re.split(r"[^A-Za-z0-9.]+", stem.lower()) if len(t) > 2]
    cands = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        low = rel.lower()
        if not low.endswith((".tif", ".zip")):
            continue
        if any(bad in low for bad in ("training_features", "labels.tif", "sample_submission",
                                     "existing_faults", "/external/", "features_u8")):
            continue
        base = path.name.lower()
        if all(tok in base for tok in toks):
            cands.append((path.stat().st_size, rel, path))
    if not cands:
        return None
    cands.sort()
    size, rel, path = cands[0]
    return rel, hashlib.sha256(path.read_bytes()).hexdigest(), size


def load_array(blob: bytes, name: str) -> np.ndarray:
    if name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            inner = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff"))][0]
            blob = zf.read(inner)
    with rasterio.open(io.BytesIO(blob)) as src:
        return src.read(1)


def measure(arr: np.ndarray, foot: np.ndarray, cat: np.ndarray, dist_cat: np.ndarray) -> dict:
    finite = np.isfinite(arr)
    pos = finite & (arr > 0) & foot
    n = int(pos.sum())
    out = {"dots_gt0": n, "footprint_pixels": int(foot.sum())}
    vals = arr[foot & finite]
    if vals.size:
        out["in_foot_min"] = round(float(vals.min()), 6)
        out["in_foot_max"] = round(float(vals.max()), 6)
        out["in_foot_mean"] = round(float(vals.mean()), 6)
    out["nan_inside_footprint"] = int((~finite & foot).sum())
    if n:
        for b in (0, 1, 2, 3, 4, 6):
            out[f"dots_beyond_{b}px_of_catalogue"] = int((pos & (dist_cat > b)).sum())
        d = dist_cat[pos]
        out["median_dist_to_catalogue_px"] = round(float(np.median(d)), 3)
        ys, xs = np.nonzero(pos)
        order = np.lexsort((xs, ys))
        ys, xs = ys[order], xs[order]
        # within-row gaps between consecutive dots (a cheap proxy for along-strand spacing)
        same_row = np.diff(ys) == 0
        gaps = np.diff(xs)[same_row]
        out["median_inrow_dot_gap_px"] = round(float(np.median(gaps)), 3) if gaps.size else None
        out["n_dot_rows_with_2plus"] = int(same_row.sum())
        out["n_unique_rows"] = int(len(np.unique(ys)))
        out["n_unique_cols"] = int(len(np.unique(xs)))
        out["value_mass"] = round(float(arr[pos].sum()), 3)
        out["n_distinct_values"] = int(np.unique(arr[foot & finite]).size)
        out["is_binary_emission"] = bool(np.allclose(arr[pos], 1.0))
        out["coverage_of_footprint"] = round(n / max(int(foot.sum()), 1), 6)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "evidence" / "org_ledger_measured.json")
    ap.add_argument("--csv", type=Path, default=ROOT / "docs" / "data" / "org-ledger-measured.csv")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    with rasterio.open(SAMPLE) as src:
        foot = np.isfinite(src.read(1))
    with rasterio.open(CATALOGUE) as src:
        cat = (src.read(1) > 0) & foot
    dist_cat = distance_transform_edt(~cat).astype(np.float32)

    jobs = LEDGER[: args.limit] if args.limit else LEDGER

    def work(job):
        site, repo, stem, score = job
        rec = {"site": site, "repo": repo, "stem": stem, "owner_reported_score": score}
        found = find_raster(site, stem)
        if not found:
            rec["status"] = "raster_not_found_in_clone"
            return rec
        path, blob_sha, size = found
        rec.update({"path": path, "sha256": blob_sha, "bytes": size})
        try:
            blob = (CACHE.parent / "repos" / site / path).read_bytes()
            rec["file_sha256"] = blob_sha
            arr = load_array(blob, path)
            if arr.shape != foot.shape:
                rec["status"] = "shape_mismatch"
                return rec
            rec.update(measure(arr, foot, cat, dist_cat))
            rec["status"] = "measured"
        except Exception as exc:  # noqa: BLE001 - record, never crash the sweep
            rec["status"] = f"error: {type(exc).__name__}: {str(exc)[:160]}"
        return rec

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        records = list(pool.map(work, jobs))

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "score_class": "USER-REPORTED / UNVERIFIED (site pages; no organizer receipt)",
        "geometry_class": "DATA-MEASUREMENT (this session, from the bytes above)",
        "catalogue_sha256": hashlib.sha256(CATALOGUE.read_bytes()).hexdigest(),
        "n_rows": len(records),
        "n_measured": sum(1 for r in records if r.get("status") == "measured"),
        "records": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        cols = ["site", "stem", "owner_reported_score", "status", "path", "file_sha256",
                "dots_gt0", "value_mass", "n_distinct_values", "is_binary_emission",
                "coverage_of_footprint", "in_foot_min", "in_foot_max",
                "dots_beyond_0px_of_catalogue", "dots_beyond_1px_of_catalogue",
                "dots_beyond_2px_of_catalogue", "dots_beyond_3px_of_catalogue",
                "dots_beyond_6px_of_catalogue", "median_dist_to_catalogue_px",
                "median_inrow_dot_gap_px", "n_unique_rows", "n_unique_cols"]
        with args.csv.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in records:
                w.writerow(r)
    print(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=2))
    for r in records:
        print(f"{r['site']:>12} {r.get('status',''):>28} score={r['owner_reported_score']:<7} "
              f"dots={r.get('dots_gt0','-'):<8} mass={r.get('value_mass','-'):<10} "
              f"b0={r.get('dots_beyond_0px_of_catalogue','-'):<7} "
              f"b2={r.get('dots_beyond_2px_of_catalogue','-'):<7} {r['stem'][:40]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
