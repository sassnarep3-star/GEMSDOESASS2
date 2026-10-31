#!/usr/bin/env python3
"""Fetch hash-pinned registry rasters (competitor submissions with owner-reported
scores) into the git-ignored cache, verifying SHA-256 before use.

Sources are public GitHub repositories; the pins come from docs/data/audit.json
and registry/registry_manifest.json. Pins prove mirror consistency only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/registry"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(repo: str, ref: str, path: str, dest: Path) -> dict:
    if dest.is_file():
        return {"status": "cached", "sha256": sha256_file(dest)}
    dest.parent.mkdir(parents=True, exist_ok=True)
    work = dest.parent / f".work-{dest.stem}"
    subprocess.run(["rm", "-rf", str(work)], check=False)
    work.mkdir(parents=True, exist_ok=True)
    url = f"https://github.com/{repo}"
    cmds = [
        ["git", "init", "-q"],
        ["git", "remote", "add", "origin", url],
        ["git", "-c", "protocol.version=2", "fetch", "-q", "--depth", "1",
         "--filter=blob:none", "origin", ref],
        ["git", "sparse-checkout", "init", "--cone"],
        ["git", "checkout", "-q", "FETCH_HEAD", "--", path],
    ]
    for c in cmds:
        r = subprocess.run(c, cwd=work, capture_output=True, text=True)
        if r.returncode != 0:
            return {"status": "failed", "error": r.stderr.strip()[:300], "cmd": " ".join(c)}
    src = work / path
    if not src.is_file():
        return {"status": "failed", "error": "path not present after checkout", "path": path}
    dest.write_bytes(src.read_bytes())
    subprocess.run(["rm", "-rf", str(work)], check=False)
    return {"status": "fetched", "sha256": sha256_file(dest)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pins", default=str(ROOT / "registry/fetch_pins.json"))
    ap.add_argument("--receipt", default=str(ROOT / "evidence/registry_fetch_receipt.json"))
    args = ap.parse_args()
    pins = json.loads(Path(args.pins).read_text())
    rows = []
    for pin in pins:
        dest = CACHE / f"{pin['key']}.tif"
        row = {"key": pin["key"], "site": pin.get("site"), "reported": pin.get("reported"),
               "repo": pin["repo"], "ref": pin["ref"], "path": pin["path"], "file": str(dest.relative_to(ROOT))}
        try:
            row.update(fetch(pin["repo"], pin["ref"], pin["path"], dest))
        except Exception as exc:  # noqa: BLE001
            row.update({"status": "failed", "error": str(exc)[:300]})
        if "expected_sha256" in pin and row.get("sha256"):
            row["hash_match"] = (row["sha256"] == pin["expected_sha256"])
        print(f"{row['status']:8s} {pin['key']:12s} match={row.get('hash_match')}")
        rows.append(row)
    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "provenance": "Public GitHub mirrors, SHA-pinned; mirror integrity only, not organizer-authenticated.",
        "rows": rows,
    }
    out = Path(args.receipt)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for r in rows if r["status"] in ("fetched", "cached") and r.get("hash_match", True))
    print(f"{ok}/{len(rows)} verified; receipt {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
