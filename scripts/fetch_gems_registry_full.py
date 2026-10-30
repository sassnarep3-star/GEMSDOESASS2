#!/usr/bin/env python3
"""Mirror every public GEMS-named GitHub repo's GeoTIFFs for the uniqueness gate.

Why: the uniqueness rule compares a candidate with every registry submission. Earlier checks
covered only nine focus sites plus local files. This script reads the explicit owner/repo list in
``research/gems_site_repos.txt`` (taken from the GitHub Pages URLs in the competition brief),
makes a blobless depth-1 clone of each repo's default branch, and copies every *.tif
with its directory structure intact, so ``scripts/focus_uniqueness_check.py`` keeps excluding
``data/`` feature stacks and bridge rasters.

Outputs (default ``~/.cache/registry_full``):
  <owner>/<repo>/<path>.tif   the GeoTIFF bytes at the default-branch HEAD at fetch time
  receipt.json                per-file SHA-256, commit SHA, timestamp, and any errors

Only github.com is contacted (git over HTTPS); no GitHub REST API quota is used.
Default-branch HEAD can change after fetch time; the receipt records the commit actually used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LIST = Path(__file__).resolve().parents[1] / "research" / "gems_site_repos.txt"


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    # Literal pathspecs: repository paths can contain glob characters such as [ ] * ?.
    env = {**os.environ, "GIT_LITERAL_PATHSPECS": "1"}
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if check and res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} failed: {res.stderr.strip()[-300:]}")
    return res.stdout


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_repo_list(path: Path) -> list[dict]:
    repos = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        owner, name = line.split("/", 1)
        repos.append({"owner": owner, "name": name, "branch": None})
    return repos


def fetch_repo(dest: Path, repo: dict) -> dict:
    work = dest / "_clones" / repo["owner"] / repo["name"]
    if work.exists():
        run(["rm", "-rf", str(work)])
    work.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{repo['owner']}/{repo['name']}.git"
    head = run(["git", "ls-remote", "--symref", url, "HEAD"]).splitlines()
    branch = next((ln.split()[1].removeprefix("refs/heads/") for ln in head if ln.startswith("ref:")), "main")
    repo = {**repo, "branch": branch}
    run(["git", "clone", "-q", "--depth", "1", "--filter=blob:none", "--no-checkout", "--branch",
         branch, url, str(work)])
    commit = run(["git", "rev-parse", "HEAD"], cwd=work).strip()
    tifs = [p for p in run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=work).splitlines()
            if p.lower().endswith((".tif", ".tiff"))]
    files = []
    if tifs:
        run(["git", "checkout", "-q", "HEAD", "--", *tifs], cwd=work)
    for rel in tifs:
        src = work / rel
        dst = dest / repo["owner"] / repo["name"] / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        files.append({"path": rel, "bytes": dst.stat().st_size, "sha256": sha256_file(dst)})
    run(["rm", "-rf", str(work)])
    return {**repo, "commit": commit, "tif_count": len(files), "files": files}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dest", type=Path, default=Path.home() / ".cache" / "registry_full")
    p.add_argument("--repos", type=Path, default=DEFAULT_LIST)
    args = p.parse_args()
    dest = args.dest.expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    repos = read_repo_list(args.repos)
    receipt = {"fetched_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "repo_list": str(args.repos), "repos_listed": len(repos), "repos": [], "errors": []}
    for repo in repos:
        try:
            receipt["repos"].append(fetch_repo(dest, repo))
        except (RuntimeError, OSError) as exc:
            receipt["errors"].append({"repo": f"{repo['owner']}/{repo['name']}", "error": str(exc)[-300:]})
        print(f"{repo['owner']}/{repo['name']}", flush=True)
    run(["rm", "-rf", str(dest / "_clones")], check=False)
    (dest / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    n_files = sum(r["tif_count"] for r in receipt["repos"])
    print(f"repos={len(receipt['repos'])} tifs={n_files} errors={len(receipt['errors'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
