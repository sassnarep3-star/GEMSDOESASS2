#!/usr/bin/env python3
"""Fetch the pinned registry rasters from their public GitHub repos and verify SHA-256.

Every file is taken from the commit SHA and path pinned in ``docs/data/audit.json``
(nine focus sites), plus the 13GEMSDOE lattice and the organizer template pinned in
the same file. Downloads are blobless, depth-1 fetches of one commit, so no default
branch can drift underneath the check. Each file's SHA-256 must equal the audit pin,
otherwise the script exits non-zero and writes nothing for that file.

Usage:
  python scripts/fetch_pinned_registry.py --dest ~/.cache/registry_pinned

Only github.com is contacted. No credentials are used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "data" / "audit.json"
OWNER = "buffedlizard55-lab"
LATTICE_REPO = "GEMSDOE24"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def fetch_one(dest_root: Path, repo: str, ref: str, rel_path: str, expect_sha: str) -> dict:
    repo_dir = dest_root / repo
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        git(["init", "-q"], repo_dir)
        git(["remote", "add", "origin", f"https://github.com/{OWNER}/{repo}.git"], repo_dir)
    git(["fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", ref], repo_dir)
    git(["checkout", "-q", "FETCH_HEAD", "--", rel_path], repo_dir)
    src = repo_dir / rel_path
    got = sha256_file(src)
    flat = dest_root / f"{repo}__{Path(rel_path).name}"
    shutil.copyfile(src, flat)
    return {
        "repo": repo,
        "ref": ref,
        "path": rel_path,
        "local_copy": str(flat),
        "sha256": got,
        "expected_sha256": expect_sha,
        "sha_match": got == expect_sha,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dest", type=Path, default=Path.home() / ".cache" / "registry_pinned")
    p.add_argument("--receipt", type=Path, default=None, help="optional JSON receipt path")
    args = p.parse_args()

    audit = json.loads(AUDIT.read_text())
    dest = args.dest.expanduser().resolve()
    dest.mkdir(parents=True, exist_ok=True)

    jobs = [(row["site"], row["ref"], row["path"], row["sha256"]) for row in audit["historical_sites"]]
    lat = audit["inputs"]["lattice"]
    jobs.append((lat["repo"], lat["ref"], lat["path"], lat["sha256"]))

    results = []
    ok = True
    for repo, ref, rel, sha in jobs:
        try:
            r = fetch_one(dest, repo, ref, rel, sha)
        except subprocess.CalledProcessError as exc:
            r = {"repo": repo, "ref": ref, "path": rel, "error": (exc.stderr or "").strip()[-300:], "sha_match": False}
        results.append(r)
        ok = ok and bool(r.get("sha_match"))
        print(f"{repo:10s} sha_match={r.get('sha_match')} {Path(rel).name}")

    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps({"dest": str(dest), "all_match": ok, "files": results}, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
