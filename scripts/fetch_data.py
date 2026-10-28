#!/usr/bin/env python3
"""Fetch owner-mirror data to an ignored cache, verifying before replacement.

SHA-256 pins establish byte consistency, not DrivenData provenance. Downloads
and multipart assembly are staged on the destination filesystem; a failed fetch,
size check or digest check leaves any existing destination intact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "registry" / "data_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(repo: str, ref: str, path: str, dest: Path) -> None:
    endpoint = f"repos/{repo}/contents/{quote(path, safe='/')}?ref={quote(ref, safe='')}"
    with dest.open("wb") as stream:
        subprocess.run(
            ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw+json"],
            stdout=stream, check=True, timeout=180,
        )


def fetch_entry(entry: dict, dest: Path) -> dict:
    """Verify a cached entry or safely stage, verify, and atomically replace it."""
    dest = Path(dest)
    expected_sha = entry["sha256"]
    expected_bytes = entry["bytes"]
    if dest.is_symlink() or (dest.exists() and not dest.is_file()):
        raise ValueError(f"Refusing to replace non-regular destination: {dest}")
    if dest.is_file() and dest.stat().st_size == expected_bytes and sha256_file(dest) == expected_sha:
        return {"id": entry["id"], "dest": entry["dest"], "group": entry["group"],
                "status": "verified", "bytes": expected_bytes, "sha256": expected_sha, "cached": True}
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{dest.name}.", dir=dest.parent) as staging:
        stage = Path(staging)
        candidate = stage / "candidate"
        if "parts" in entry:
            with candidate.open("wb") as assembled:
                for index, source in enumerate(entry["parts"]):
                    part = stage / f"part-{index:03d}"
                    _download(entry["repo"], entry["ref"], source, part)
                    with part.open("rb") as src:
                        for block in iter(lambda: src.read(1 << 20), b""):
                            assembled.write(block)
        else:
            _download(entry["repo"], entry["ref"], entry["path"], candidate)
        size = candidate.stat().st_size
        digest = sha256_file(candidate)
        if size != expected_bytes or digest != expected_sha:
            raise ValueError(f"Pinned data mismatch for {entry['id']}: size={size}, sha256={digest}; destination not replaced")
        os.replace(candidate, dest)
    return {"id": entry["id"], "dest": entry["dest"], "group": entry["group"],
            "status": "verified", "bytes": size, "sha256": digest, "cached": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=str(ROOT / ".cache/gems_data"), help="Directory for cached owner-mirror data")
    parser.add_argument("--receipt", default=str(ROOT / "data/restore_receipt.json"), help="JSON verification receipt")
    args = parser.parse_args()
    dest = Path(args.dest).resolve()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    rows = []
    for entry in manifest["files"]:
        target = dest / entry["dest"]
        if not target.parent.resolve().is_relative_to(dest):
            raise ValueError(f"Destination escapes cache root: {entry['dest']}")
        try:
            row = fetch_entry(entry, target)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            row = {"id": entry["id"], "dest": entry["dest"], "group": entry["group"],
                   "status": "failed", "error": str(error)}
        rows.append(row)
        print(f"{row['status'].upper():8s} {entry['id']}")
    failed = sum(row["status"] != "verified" for row in rows)
    receipt = {
        "schema_version": 3,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "storage_root": str(dest),
        "provenance": "Owner-mirror hash integrity only; not an authenticated organizer download.",
        "verified_files_count": len(rows) - failed, "failed_files_count": failed, "files": rows,
    }
    receipt_path = Path(args.receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=receipt_path.parent,
                                     prefix=f".{receipt_path.name}.", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            json.dump(receipt, stream, indent=2, allow_nan=False)
            stream.write("\n")
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, receipt_path)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Receipt written to {receipt_path}: {len(rows) - failed} verified, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
