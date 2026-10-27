#!/usr/bin/env python3
"""Fetch and SHA-256 verify all 33 hash-pinned core, external, and scored competition datasets.

Uses GitHub REST/raw streaming against immutable SHA-256 pins in ``registry/data_manifest.json``
so the entire pipeline runs autonomously without manual login walls, while keeping large binaries
inside ``.cache/gems_data`` (git-ignored) and writing an auditable receipt to ``data/restore_receipt.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "registry" / "data_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(repo: str, ref: str, path: str, dest: Path, want_sha: str | None = None) -> Path:
    dest = Path(dest)
    if want_sha and dest.exists() and sha256_file(dest) == want_sha:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with tmp.open("wb") as fh:
        subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}", "-H", "Accept: application/vnd.github.raw"],
            stdout=fh,
            check=True,
        )
    tmp.replace(dest)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch and SHA-256 verify GEMS competition datasets.")
    ap.add_argument("--dest", default=str(ROOT / ".cache" / "gems_data"), help="Destination directory for cached data")
    ap.add_argument("--receipt", default=str(ROOT / "data" / "restore_receipt.json"), help="JSON verification receipt")
    args = ap.parse_args()

    dest = Path(args.dest)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ok_rows, bad_rows = [], []

    for entry in manifest["files"]:
        target = dest / entry["dest"]
        if not (target.exists() and sha256_file(target) == entry["sha256"]):
            if "parts" in entry:
                chunks = []
                for idx, part_path in enumerate(entry["parts"]):
                    cpath = dest / f".part-{entry['id']}-{idx:03d}"
                    chunks.append(gh_raw(entry["repo"], entry["ref"], part_path, cpath))
                target.parent.mkdir(parents=True, exist_ok=True)
                tmp = target.with_suffix(target.suffix + ".tmp")
                with tmp.open("wb") as out:
                    for cpath in chunks:
                        with cpath.open("rb") as cfh:
                            for block in iter(lambda: cfh.read(1 << 20), b""):
                                out.write(block)
                        cpath.unlink(missing_ok=True)
                tmp.replace(target)
            else:
                gh_raw(entry["repo"], entry["ref"], entry["path"], target, want_sha=entry["sha256"])

        digest = sha256_file(target)
        size = target.stat().st_size
        matched = digest == entry["sha256"] and size == entry["bytes"]
        row = {
            "id": entry["id"],
            "dest": entry["dest"],
            "group": entry["group"],
            "status": "verified" if matched else "mismatch",
            "bytes": size,
            "sha256": digest,
        }
        (ok_rows if matched else bad_rows).append(row)
        print(f"{'OK  ' if matched else 'FAIL'} {entry['id']:35s} {size:11,d} B  {digest[:16]}...")

    receipt = {
        "schema_version": 2,
        "verified_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "storage_root": ".cache/gems_data",
        "verified_files_count": len(ok_rows),
        "failed_files_count": len(bad_rows),
        "files": ok_rows + bad_rows,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Receipt written to {receipt_path}: {len(ok_rows)} verified, {len(bad_rows)} failed.")
    return 1 if bad_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
