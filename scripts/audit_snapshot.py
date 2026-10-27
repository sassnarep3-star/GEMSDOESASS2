#!/usr/bin/env python3
"""Reproduce a pinned historical-raster audit, not a model experiment.

Downloads public, owner-hosted mirror files through the GitHub API and verifies
all bytes against research/priority_sources.json. The input template is NOT an
authenticated organizer file. Outputs are historical measurements and must not
be used to authorize an upload or substitute for the complete live registry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from urllib.parse import quote

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "research" / "priority_sources.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_pinned(spec: dict, cache_file: Path, fetch: bool) -> Path:
    """Use pinned ref AND hash. Never accept stale, partial or wrong bytes."""
    expected = spec["sha256"]
    if cache_file.exists() and sha256_file(cache_file) == expected:
        return cache_file
    if not fetch:
        raise ValueError(f"Missing or wrong-hash input: {cache_file}")
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache_file.with_suffix(cache_file.suffix + ".partial")
    repo = spec.get("repo") or spec["site"]
    owner = spec.get("owner", "buffedlizard55-lab")
    endpoint = (
        f"repos/{owner}/{repo}/contents/{quote(spec['path'], safe='/')}"
        f"?ref={quote(spec['ref'], safe='')}"
    )
    try:
        with tmp.open("wb") as fp:
            proc = subprocess.run(
                ["gh", "api", "-H", "Accept: application/vnd.github.raw+json", endpoint],
                stdout=fp, stderr=subprocess.PIPE, check=False,
            )
        if proc.returncode:
            raise RuntimeError(f"GitHub fetch failed for {endpoint}: {proc.stderr.decode(errors='replace')}")
        actual = sha256_file(tmp)
        if actual != expected:
            raise ValueError(f"Hash mismatch for {endpoint}: expected {expected}, got {actual}")
        os.replace(tmp, cache_file)
    finally:
        tmp.unlink(missing_ok=True)
    return cache_file


def forced_overlap(allowed_pixels: int, dots: int, limit: Fraction = Fraction(7, 10),
                   footprint_pixels: int | None = None) -> dict:
    """Pigeonhole lower bound for distinct pixels, with exact threshold arithmetic.

    `allowed_pixels` are footprint cells farther than 3 px from one registry
    raster. Does NOT prove a candidate with fewer dots is unique.
    """
    if allowed_pixels < 0 or dots <= 0 or not 0 <= limit < 1:
        raise ValueError("invalid allowed pixels, dot count, or overlap limit")
    if footprint_pixels is not None and (footprint_pixels <= 0 or allowed_pixels > footprint_pixels or dots > footprint_pixels):
        raise ValueError("allowed pixels or distinct dots exceed the footprint")
    forced = max(0, dots - allowed_pixels)
    return {
        "dots": dots,
        "minimum_overlapping_dots": forced,
        "minimum_overlap_fraction": forced / dots,
        "necessarily_exceeds_limit": Fraction(forced, dots) > limit,
        "first_failing_dot_count": math.floor(Fraction(allowed_pixels, 1) / (1 - limit)) + 1,
    }


def check_aligned(ds: rasterio.io.DatasetReader, template: rasterio.io.DatasetReader, name: str) -> None:
    if (ds.shape, ds.crs, ds.transform, ds.count) != (template.shape, template.crs, template.transform, 1):
        raise ValueError(f"{name} does not match template geometry or band count")


def binary_mask(path: Path, template: rasterio.io.DatasetReader, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        check_aligned(ds, template, path.name)
        arr = ds.read(1)
        inside = arr[foot]
        if (not np.all(np.isfinite(inside)) or not np.all((inside == 0) | (inside == 1))
                or not np.all(ds.read_masks(1)[foot] > 0)):
            raise ValueError(f"{path} is not an unmasked finite binary mask inside the footprint")
        # Discarding out-of-footprint positive reference pixels could otherwise
        # undercount overlap for a candidate near the boundary.
        if np.any(np.isfinite(arr[~foot]) & (arr[~foot] > 0)):
            raise ValueError(f"{path} has positive pixels outside the template footprint")
        return foot & (arr == 1)


def overlap_fraction(candidate: np.ndarray, neighborhood: np.ndarray) -> dict:
    n = int(np.count_nonzero(candidate))
    if not n:
        raise ValueError("Empty candidate has undefined directional overlap")
    n_overlap = int(np.count_nonzero(candidate & neighborhood))
    return {"candidate_dots": n, "dots_within_3px": n_overlap, "fraction": n_overlap / n}


def audit(config: dict, cache: Path, fetch: bool = True) -> dict:
    paths = {}
    for key, spec in config["inputs"].items():
        filename = "sample_submission.tif" if key == "template" else f"{key}.tif"
        paths[key] = fetch_pinned(spec, cache / filename, fetch)
    for site in config["sites"]:
        paths[site["site"]] = fetch_pinned(site, cache / (site["site"] + ".tif"), fetch)
    for w in config["witnesses"]:
        paths[w["id"]] = fetch_pinned(w, cache / (w["id"] + ".tif"), fetch)

    with rasterio.open(paths["template"]) as template:
        sample = template.read(1)
        foot = np.isfinite(sample) & (template.read_masks(1) > 0)
        if not foot.any():
            raise ValueError("Template footprint is empty")
        with rasterio.open(paths["labels"]) as ds:
            check_aligned(ds, template, "labels")
            labels = (ds.read(1) == 1) & foot
        masks = {s["site"]: binary_mask(paths[s["site"]], template, foot) for s in config["sites"]}
        witnesses = {w["id"]: binary_mask(paths[w["id"]], template, foot) for w in config["witnesses"]}
        lattice = binary_mask(paths["lattice"], template, foot)
        grid = {"shape": list(template.shape), "crs": str(template.crs),
                "transform": list(template.transform)[:6], "footprint_pixels": int(foot.sum())}

    if not lattice.any():
        raise ValueError("Empty lattice cannot witness the uniqueness stop")
    lattice_near = distance_transform_edt(~lattice) <= 3
    far = int(np.count_nonzero(foot & ~lattice_near))
    matrix = {}
    for reference, mask in masks.items():
        if not mask.any():
            raise ValueError(f"Empty reference: {reference}")
        near = distance_transform_edt(~mask) <= 3
        for candidate, cand_mask in masks.items():
            if candidate != reference:
                matrix[f"{candidate} -> {reference}"] = overlap_fraction(cand_mask, near)

    historical = []
    for site in config["sites"]:
        name = site["site"]
        matches = [(key.split(" -> ")[1], val) for key, val in matrix.items() if key.startswith(name + " -> ")]
        max_peer, max_val = max(matches, key=lambda item: item[1]["fraction"])
        historical.append({
            **site,
            "artifact_url": f"https://github.com/buffedlizard55-lab/{name}/blob/{site['ref']}/{site['path']}",
            "dot_count": int(masks[name].sum()),
            "max_overlap_peer": max_peer,
            "max_overlap_fraction": max_val["fraction"],
            "unique_against_nine_under_dot_rule": max_val["fraction"] <= 0.70,
            "historical_score_evidence": "USER-REPORTED / UNVERIFIED; no organizer receipt linking these bytes",
        })

    witness_results = []
    for w in config["witnesses"]:
        result = overlap_fraction(witnesses[w["id"]], lattice_near)
        witness_results.append({
            **w, **result, "fails_literal_overlap_rule": result["fraction"] > 0.70,
            "artifact_url": f"https://github.com/{w.get('owner', 'buffedlizard55-lab')}/{w.get('repo', w['site'])}/blob/{w['ref']}/{w['path']}",
        })

    d28, b2, solo = masks["GEMSDOE25"], masks["GEMSDOE32"], masks["GEMSDOE31"]
    if not labels.any():
        raise ValueError("Empty catalogue cannot support the prune comparison")
    dist_known = distance_transform_edt(~labels)
    lineage = {
        "GEMSDOE25_vs_GEMSDOE30_xor_pixels": int(np.count_nonzero(d28 ^ masks["GEMSDOE30"])),
        "GEMSDOE32_vs_GEMSDOE25_pruned_within_2px_xor_pixels": int(np.count_nonzero(b2 ^ (d28 & (dist_known > 2)))),
        "GEMSDOE25_dots_removed_within_2px": int(np.count_nonzero(d28 & (dist_known <= 2))),
        "GEMSDOE31_vs_GEMSDOE25_pruned_within_1px_xor_pixels": int(np.count_nonzero(solo ^ (d28 & (dist_known > 1)))),
        "GEMSDOE25_dots_removed_within_1px": int(np.count_nonzero(d28 & (dist_known <= 1))),
        "GEMSDOE31_dots_not_in_GEMSDOE32": int(np.count_nonzero(solo & ~b2)),
        "GEMSDOE32_dots_not_in_GEMSDOE31": int(np.count_nonzero(b2 & ~solo)),
    }
    return {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "scope": f"This independent audit only: pinned owner mirrors, {len(historical)} historical variants and {len(witness_results)} existing candidate-file witnesses; no new model experiment or authenticated score receipt. Parallel branches produced research TIFFs and reported separate experiments.",
        "important_limit": "The complete current registry and pre-placement surfaces were not audited. Passing this snapshot cannot establish uniqueness or authorize submission.",
        "inputs": config["inputs"], "main_refs_observed_utc": config["main_refs_observed_utc"],
        "grid": grid,
        "lattice": {"registry_reference": "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
                    "positive_pixels": int(lattice.sum()), "footprint_within_3px": int(np.count_nonzero(foot & lattice_near)),
                    "footprint_farther_than_3px": far,
                    "bound_at_37654": forced_overlap(far, 37654, footprint_pixels=int(foot.sum()))},
        "historical_sites": historical, "directional_overlap": matrix,
        "lineage_analysis": lineage, "existing_candidate_witnesses": witness_results,
        "new_experiments": 0, "new_tiff_created": False, "weekly_slots_spent": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cache", type=Path, default=ROOT / ".cache" / "priority")
    p.add_argument("--out", type=Path, default=ROOT / "docs" / "data" / "audit.json")
    p.add_argument("--no-fetch", action="store_true", help="Fail rather than fetch missing hash-pinned inputs")
    args = p.parse_args()
    config = json.loads(CONFIG.read_text())
    result = audit(config, args.cache, fetch=not args.no_fetch)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".partial")
    try:
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        temporary.replace(args.out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {args.out}; {len(result['directional_overlap'])} directed comparisons; no candidate generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
