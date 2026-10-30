#!/usr/bin/env python3
"""Fetch the nine focus-site files pinned in README.md at their pinned commits.

The registry builder lists HEAD trees only, so the pinned files are fetched separately
through the GitHub contents API (`?ref=<commit>`). Each download is verified against the
git blob SHA-1 reported by the API and then re-hashed locally.

Writes: registry/focus_pins.json  (repo, commit, path, blob, sha256, bytes)
        cache: ~/.cache/registry/focus/<site>.tif
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = Path(os.environ.get("GEMS_REGISTRY", str(Path.home() / ".cache" / "registry"))) / "focus"
OUT = ROOT / "registry" / "focus_pins.json"

# (site, repo, pinned commit, path) — transcribed from README.md "Nine-site executive summary"
PINS = [
    ("GEMSDOE32", "buffedlizard55-lab/GEMSDOE32", "400b60d4a6d99f425ee90504e6c4552227556dd1", "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    ("GEMSDOE36", "buffedlizard55-lab/GEMSDOE36", "32c2660001d98f6fa9084a0971b3a9d5062d49b9", "docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
    ("GEMSDOE28", "buffedlizard55-lab/GEMSDOE28", "2c839d10f57ec9b074829e93c84bc39935f52896", "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif"),
    ("GEMSDOE31", "buffedlizard55-lab/GEMSDOE31", "eeb7da54ca4a8ae056f45e5b23eeef586ad79bf2", "docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif"),
    ("GEMSDOE33", "buffedlizard55-lab/GEMSDOE33", "efa438d3104893c3e8aedf3817ac22167b1c681a", "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif"),
    ("GEMSDOE25", "buffedlizard55-lab/GEMSDOE25", "b4e74b3f9b191fbc214b6447e9ff1f3fa67552c4", "docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif"),
    ("GEMSDOE30", "buffedlizard55-lab/GEMSDOE30", "9c0d637c0171407196b61b780444bc772ce75438", "docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif"),
    ("GEMSDOE24", "buffedlizard55-lab/GEMSDOE24", "a433b430b74b813a9118ebd4ec438b12cbc69f46", "docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif"),
    ("GEMSDOE27", "buffedlizard55-lab/GEMSDOE27", "bef7ae8e8f63b69d299c9214c75988c8f5055f9c", "docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif"),
]


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def gh_json(args: list[str]) -> dict:
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} failed: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for site, repo, commit, path in PINS:
        meta = gh_json([f"repos/{repo}/contents/{path}?ref={commit}"])
        raw = base64.b64decode(meta["content"]) if meta.get("content") else None
        if raw is None or meta.get("encoding") not in (None, "base64"):
            raw = gh_json([f"repos/{repo}/git/blobs/{meta['sha']}"]).get("content")
            raw = base64.b64decode(raw)
        blob = meta["sha"]
        if git_blob_sha1(raw) != blob:
            raise RuntimeError(f"{site}: blob SHA-1 mismatch")
        dest = CACHE / f"{site}.tif"
        dest.write_bytes(raw)
        rows.append({
            "site": site, "repo": repo, "commit": commit, "path": path, "blob": blob,
            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "cached_at": str(dest),
        })
        print(f"{site}: {len(raw)} B blob={blob[:12]} sha256={rows[-1]['sha256'][:12]}")
    OUT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "GitHub contents API ?ref=<pinned commit>; blob SHA-1 verified",
        "files": rows,
    }, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
