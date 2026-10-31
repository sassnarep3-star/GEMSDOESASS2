#!/usr/bin/env python3
"""Fetch additional owner-reported scored rasters (calibration anchors) from the
public GEMSDOE site repositories, matching each by file-name substring.

Every row names the site, the owner-reported score (USER-REPORTED / UNVERIFIED)
and the substring used to locate the artifact.  Anything unfound is recorded as
an error, never silently skipped.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache/registry/anchors"
OWNER = "buffedlizard55-lab"

# (site_key, reported_score, filename_substring)  -- scores are owner-reported in the brief.
ANCHORS = [
    ("GEMSDOE10", 0.1839, "h28-dotted-ridge-20260928T020256236880Z"),
    ("19GEMSDOE", 0.1922, "h19-5-powerlaw-budget-multiline-corroborated-20260930"),
    ("19GEMSDOE", 0.1894, "h19-4-multiline-corroborated-openness-thermal-pop"),
    ("16GEMSDOE", 0.1855, "h16-1-topo-geophys-baseline-ridges-20260930"),
    ("GEMSDOE49", 0.2376, "gate_ortho_w0.25-40k-20261006T213721Z"),
    ("GEMSDOE70", 0.2478, "gems70-p5-dual-submod300-oof38k"),
    ("GEMSDOE63", 0.2303, "cvarlw-thin-s3p17-54864"),
    ("GEMSDOE76", 0.2343, "gems76-ptcf-tiltworm-submod39k"),
    ("GEMSDOE48", 0.2296, "h59-cover-ds-belief-b2xh33d"),
    ("GEMSDOE73", 0.1917, "gems73-h73-mcsc-seamfree-blakely"),
    ("GEMSDOE82", 0.1886, "h82-submodular-punoisyor"),
    ("GEMSDOE91", 0.1823, "gems91-s17-lftg"),
    ("GEMSDOE27", 0.2250, "gems27-h31-drcg-wl-celf28"),
    ("GEMSDOE27", 0.2190, "gems27-h29-hydrothermal-piedmont-celf"),
    ("GEMSDOE30", 0.1462, "gems30-MSDB1-edge44090"),
    ("GEMSDOE85", 0.1110, "hjcd-ventbridge-submod"),
    ("GEMSDOE87", 0.0500, "h87-h87-cmgep"),
    ("GEMSDOE78", 0.1564, "gems78-h78sigx-fuse-b5"),
    ("GEMSDOE12", 0.1294, "r7-nms3-dem10-scarp"),
    ("GEMSDOE90", 0.0749, "gems90-cnc-35000dots"),
    ("GEMSDOE92", 0.0255, "gemsdoe92-listricdip-updip50"),
    ("GEMSDOE26", 0.1223, "dilcond-oof-v1"),
    ("GEMSDOE22", 0.1002, "h23-a-dti-optimal-emission-6pct"),
    ("GEMSDOE23", 0.1352, "h30-arrangement-matched-habitat"),
    ("GEMSDOE13", 0.0904, "r13-lattice-s5_v2"),
    ("GEMSDOE15", 0.0782, "conj_alteration_mag"),
    ("GEMSDOE37", 0.1193, "h6-physics-dotted-80k"),
    ("GEMSDOE42", 0.0581, "xscale-worm-persistence"),
    ("GEMSDOE40", 0.0984, "h45-eulerdepthreadcluster"),
    ("GEMSDOE51", 0.1047, "h53-twostage"),
    ("GEMSDOE52", 0.0856, "h97b-candidate"),
    ("GEMSDOE75", 0.1627, "trlt-radon-loco-ridge"),
    ("GEMSDOE83", 0.0573, "gvcd-dink300"),
    ("GEMSDOE89", 0.0301, "bh-rtp-habc"),
    ("GEMSDOE9", 0.0107, "2314b599"),
    ("GEMSDOE14", 0.0020, "r5-geom-horse-ensemble"),
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def clone(repo: str, work: Path) -> tuple[bool, str]:
    work.mkdir(parents=True, exist_ok=True)
    for c in (["git", "init", "-q"],
              ["git", "remote", "add", "origin", f"https://github.com/{OWNER}/{repo}"],
              ["git", "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", "HEAD"],
              ["git", "sparse-checkout", "init", "--cone"],
              ["git", "checkout", "-q", "FETCH_HEAD", "--", "docs"]):
        r = subprocess.run(c, cwd=work, capture_output=True, text=True)
        if r.returncode != 0:
            return False, r.stderr.strip()[:200]
    return True, ""


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    by_repo: dict[str, Path] = {}
    for site, score, sub in ANCHORS:
        row = {"site": site, "reported": score, "substring": sub, "repo": f"{OWNER}/{site}"}
        if site not in by_repo:
            work = CACHE / f".work-{site}"
            subprocess.run(["rm", "-rf", str(work)], check=False)
            ok, err = clone(site, work)
            if not ok:
                row.update(status="failed", error=err)
                print(f"failed  {site:12s} {err[:80]}")
                rows.append(row)
                continue
            by_repo[site] = work
        work = by_repo[site]
        hits = sorted(p for p in work.rglob("*.tif") if sub.lower() in p.name.lower() and ".zip" not in p.suffixes)
        if not hits:
            hits = sorted(p for p in work.rglob("*.tif") if sub.lower().replace("-", "") in p.name.lower().replace("-", ""))
        if not hits:
            row.update(status="not_found")
            print(f"missing {site:12s} {sub}")
            rows.append(row)
            continue
        src = hits[0]
        dest = CACHE / f"{site}--{score}--{src.name}"
        dest.write_bytes(src.read_bytes())
        row.update(status="fetched", file=str(dest.relative_to(ROOT)), bytes=dest.stat().st_size,
                   sha256=sha256_file(dest))
        print(f"ok      {site:12s} {score}  {src.name}")
        rows.append(row)
    for work in by_repo.values():
        subprocess.run(["rm", "-rf", str(work)], check=False)
    out = ROOT / "evidence/anchor_fetch_receipt.json"
    out.write_text(json.dumps({
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "provenance": "Public GitHub mirrors at default-branch HEAD; scores are OWNER-REPORTED / UNVERIFIED. "
                      "HEAD-ref pins are weaker than the 9 focus-site SHA pins: a file may have changed since scoring.",
        "rows": rows,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(1 for r in rows if r.get('status')=='fetched')}/{len(rows)} fetched -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
