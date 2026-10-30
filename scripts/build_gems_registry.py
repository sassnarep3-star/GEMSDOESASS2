#!/usr/bin/env python3
"""Rebuild the GEMSDOE comparison registry from public GitHub sources.

Why: the uniqueness gate (3-px dot overlap and rank correlation against every
prior GEMSDOE submission raster) must be reproducible. The earlier registry cache
lived in ~/.cache and was not persisted, so its receipts could not be re-checked.

What it does (all public, no credentials beyond the sandbox `gh` login):
  1. Reads ``registry/site_list.txt`` (every GEMSDOE repo named in the project prompt).
  2. Resolves each repo's default-branch HEAD commit with ``git ls-remote``.
  3. Lists GeoTIFFs in each HEAD tree via the GitHub API, excluding ``data/``
     directories (feature stacks / labels) per the project's registry protocol.
  4. Downloads each *unique* blob once through the GitHub blob API and verifies
     it against its git blob SHA-1 (content integrity, independent of the host).
  5. Reads each raster header/statistics with rasterio and writes
     ``registry/gems_registry_manifest.json`` (committed; small) plus a
     ``registry/gems_registry_listing.tsv``.

Raw rasters go to ``$GEMS_REGISTRY`` (default ``~/.cache/registry``), which is
git-ignored and not persisted. Re-run this script to rebuild them.

Usage:
  python scripts/build_gems_registry.py            # list + download + manifest
  python scripts/build_gems_registry.py --list-only
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE_LIST = ROOT / "registry" / "site_list.txt"
MANIFEST = ROOT / "registry" / "gems_registry_manifest.json"
LISTING = ROOT / "registry" / "gems_registry_listing.tsv"
CACHE = Path(os.environ.get("GEMS_REGISTRY", str(Path.home() / ".cache" / "registry")))
BLOBS = CACHE / "blobs"

TEMPLATE_SHAPE = (3730, 3292)
TEMPLATE_CRS = "EPSG:32611"
TEMPLATE_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
MAX_BLOB_BYTES = 60_000_000  # 60 MB guard; larger blobs are listed but not downloaded


def run(cmd: list[str], retries: int = 6) -> bytes:
    """Run a command, retrying with back-off when the GitHub API rate-limits us."""
    delay = 20
    for attempt in range(retries):
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode == 0:
            return proc.stdout
        err = proc.stderr.decode(errors="replace")
        if "rate limit" in err.lower() or "403" in err or "secondary" in err.lower():
            time.sleep(delay)
            delay = min(delay * 2, 600)
            continue
        raise RuntimeError(f"{' '.join(cmd[:4])} failed: {err.strip()[:300]}")
    raise RuntimeError(f"gave up after {retries} attempts: {' '.join(cmd[:4])}")


def repos() -> list[str]:
    return [ln.strip() for ln in SITE_LIST.read_text().splitlines() if ln.strip()]


def head_sha(repo: str) -> str:
    out = subprocess.run(
        ["git", "ls-remote", f"https://github.com/{repo}", "HEAD"],
        capture_output=True, text=True, timeout=120,
    ).stdout.split()
    if not out:
        raise RuntimeError(f"cannot resolve HEAD for {repo}")
    return out[0]


def list_tifs(repo: str, commit: str) -> tuple[list[dict], int]:
    """Return (tif entries outside data/, count of excluded data/ tifs)."""
    tree = json.loads(run(["gh", "api", f"repos/{repo}/git/trees/{commit}?recursive=1"]))
    entries, excluded = [], 0
    for node in tree.get("tree", []):
        path = node.get("path", "")
        if not path.lower().endswith((".tif", ".tiff")):
            continue
        if path.startswith("data/") or "/data/" in path:
            excluded += 1
            continue
        entries.append({"repo": repo, "commit": commit, "path": path,
                        "blob": node["sha"], "size": node.get("size", -1)})
    return entries, excluded


def fetch_blob(blob: str, size: int) -> Path:
    dest = BLOBS / f"{blob}.tif"
    if dest.exists() and dest.stat().st_size == size:
        return dest
    data = run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                f"repos/{REPO_FOR_BLOB[blob]}/git/blobs/{blob}"])
    git_id = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if git_id != blob:
        raise RuntimeError(f"blob {blob} failed git SHA-1 integrity check")
    tmp = dest.with_suffix(".partial")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return dest


REPO_FOR_BLOB: dict[str, str] = {}


def describe(path: Path, blob: str) -> dict:
    import numpy as np
    import rasterio

    with rasterio.open(path) as ds:
        a = ds.read(1)
        crs = ds.crs.to_string() if ds.crs else None
        tr = tuple(ds.transform)[:6]
        shape = [ds.height, ds.width]
    finite = np.isfinite(a)
    pos = finite & (a > 0.5)
    eligible = (
        tuple(shape) == TEMPLATE_SHAPE
        and crs == TEMPLATE_CRS
        and all(abs(x - y) < 1e-6 for x, y in zip(tr, TEMPLATE_TRANSFORM))
    )
    return {
        "blob": blob,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "shape": shape,
        "crs": crs,
        "transform": list(tr),
        "dtype": str(a.dtype),
        "n_finite": int(finite.sum()),
        "n_positive": int(pos.sum()),
        "values_in_0_1": bool(((a[finite] >= 0) & (a[finite] <= 1)).all()) if finite.any() else None,
        "eligible_template_grid": bool(eligible),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list-only", action="store_true")
    args = ap.parse_args()
    BLOBS.mkdir(parents=True, exist_ok=True)

    listing: list[dict] = []
    excluded_total = 0
    heads: dict[str, str] = {}
    errors: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(lambda r: (r, head_sha(r)), r): r for r in repos()}
        for f in cf.as_completed(futs):
            try:
                r, sha = f.result()
                heads[r] = sha
            except Exception as exc:  # record, do not hide
                errors.append({"repo": futs[f], "stage": "ls-remote", "error": str(exc)[:200]})
    for repo in repos():
        if repo not in heads:
            continue
        try:
            entries, excl = list_tifs(repo, heads[repo])
        except Exception as exc:
            errors.append({"repo": repo, "stage": "tree", "error": str(exc)[:200]})
            continue
        excluded_total += excl
        listing.extend(entries)

    with LISTING.open("w") as fh:
        fh.write("repo\tcommit\tpath\tblob\tsize\n")
        for e in listing:
            fh.write(f"{e['repo']}\t{e['commit']}\t{e['path']}\t{e['blob']}\t{e['size']}\n")

    unique: dict[str, dict] = {}
    for e in listing:
        unique.setdefault(e["blob"], e)
        REPO_FOR_BLOB.setdefault(e["blob"], e["repo"])
    print(f"repos={len(heads)} tif_entries={len(listing)} unique_blobs={len(unique)} "
          f"excluded_data_tifs={excluded_total} errors={len(errors)}", file=sys.stderr)
    if args.list_only:
        return 0

    todo = [e for e in unique.values() if e["size"] <= MAX_BLOB_BYTES]
    skipped_big = [e["blob"] for e in unique.values() if e["size"] > MAX_BLOB_BYTES]
    described: dict[str, dict] = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(fetch_blob, e["blob"], e["size"]): e for e in todo}
        done = 0
        for f in cf.as_completed(futs):
            e = futs[f]
            try:
                path = f.result()
                described[e["blob"]] = describe(path, e["blob"])
            except Exception as exc:
                errors.append({"blob": e["blob"], "repo": e["repo"], "path": e["path"],
                               "stage": "download/describe", "error": str(exc)[:200]})
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(todo)} blobs", file=sys.stderr)

    entries_out = []
    for e in listing:
        d = described.get(e["blob"])
        entries_out.append({
            "repo": e["repo"], "commit": e["commit"], "path": e["path"],
            "blob": e["blob"], "size": e["size"],
            **({k: v for k, v in d.items() if k != "blob"} if d else {"described": False}),
        })

    manifest = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "template": {"shape": list(TEMPLATE_SHAPE), "crs": TEMPLATE_CRS,
                     "transform": list(TEMPLATE_TRANSFORM)},
        "source": "GitHub HEAD trees of every repo in registry/site_list.txt; blobs verified by git SHA-1",
        "repos_resolved": heads,
        "excluded_data_tifs": excluded_total,
        "blobs_over_size_guard_not_downloaded": skipped_big,
        "errors": errors,
        "entries": entries_out,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"wrote {MANIFEST} entries={len(entries_out)} errors={len(errors)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
