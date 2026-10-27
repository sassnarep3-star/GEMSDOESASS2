#!/usr/bin/env python3
"""Fetch hash-pinned peer-mirror CDCC research inputs (never official data)."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def github_json(path: str) -> dict:
    request = Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "GEMSDOESASS2-research-input-fetch"},
    )
    with urlopen(request, timeout=180) as response:  # noqa: S310 -- fixed GitHub API host
        return json.load(response)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=root / "registry" / "cdcc_research_input_manifest.json")
    parser.add_argument("--output-dir", type=Path, default=root / "data" / "cache" / "cdcc_research_mirror")
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest.get("schema") != "gemsdoesass2-cdcc-research-input-v1":
        raise SystemExit("Unexpected input manifest schema")
    repository = manifest["repository"]
    receipt = {"manifest": str(args.manifest), "official_data": False, "entries": []}
    for entry in manifest["inputs"]:
        output = args.output_dir / entry["local_filename"]
        if output.is_file() and hashlib.sha256(output.read_bytes()).hexdigest() == entry["sha256"]:
            reused = True
        else:
            payload = github_json(f"/repos/{repository}/git/blobs/{entry['git_blob_sha']}")
            if payload.get("encoding") != "base64":
                raise SystemExit(f"Unexpected blob encoding for {entry['role']}")
            data = base64.b64decode(payload["content"])
            actual = hashlib.sha256(data).hexdigest()
            if actual != entry["sha256"]:
                raise SystemExit(f"SHA mismatch for {entry['role']}: {actual}")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)
            reused = False
        receipt["entries"].append(
            {"role": entry["role"], "path": str(output), "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "reused": reused}
        )
    receipt["pass"] = all(
        row["sha256"] == item["sha256"] for row, item in zip(receipt["entries"], manifest["inputs"], strict=True)
    )
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text)
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
