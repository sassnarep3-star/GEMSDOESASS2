#!/usr/bin/env python3
"""Measured receipts for the two gates that decide the 0.2778 question and the unique file.

1. LATTICE GATE (protocol rule: >70% of a submission's dots within 3 px of one registry
   raster's dots => duplicate). The registry raster is the pinned 13GEMSDOE lattice
   (GEMSDOE24 @ a433b430, sha256 b4570b40...), which is on the user's own registry list
   (13GEMSDOE, 20261001_r13-lattice-s5_v2_nan-outside). We measure every candidate and the
   nine focus-site bests against it and report how many footprint cells the lattice leaves
   uncovered (>3 px away). Any candidate must place >=30% of its dots on those cells to pass.

2. LINEAGE + MARGINAL RULE for the 0.2778 autopsy. We test pixel-exact set relations between
   GEMSDOE25 (44,090 dots), GEMSDOE32 (37,654 dots) and the catalogue, and check the identity
   used to reason about dot value: for a Tversky-type ratio with alpha + beta = 1, removing a
   dot whose expected hit probability is q raises DTI iff q < alpha * DTI. The identity is
   checked numerically on random (TP, FP, FN) triples.

No score is computed here. Scores in the output are copied labels only.
Usage: .venv/bin/python scripts/verify_gate_and_lineage.py --cache /tmp/gems_focus_cache
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_focus_sites import URL_RE, extract_member, fetch_tarball  # noqa: E402

LATTICE_PIN = {
    "repo": ("buffedlizard55-lab", "GEMSDOE24", "a433b430b74b813a9118ebd4ec438b12cbc69f46"),
    "path": "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
    "sha256": "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2",
}
ALPHA, BETA = 0.2, 0.8
RADIUS = 3.0
OUT = REPO / "docs" / "data" / "gate-and-lineage-recheck.json"


def dots_from(data: bytes, footprint: np.ndarray) -> np.ndarray:
    with rasterio.MemoryFile(data) as mf, mf.open() as src:
        a = src.read(1)
    a = np.where(np.isfinite(a), a, 0)
    return footprint & (a > 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, default=Path("/tmp/gems_focus_cache"))
    args = ap.parse_args()

    with rasterio.open(REPO / "data/bridge/labels.tif") as s:
        footprint = s.read_masks(1) > 0
        labels = s.read(1)
    catalogue = footprint & (labels == 1)
    dist_cat = distance_transform_edt(~catalogue)

    owner, repo, sha = LATTICE_PIN["repo"]
    tb = fetch_tarball(owner, repo, sha, args.cache)
    lat_bytes = extract_member(tb, LATTICE_PIN["path"])
    lat_sha = hashlib.sha256(lat_bytes).hexdigest()
    with rasterio.MemoryFile(lat_bytes) as mf, mf.open() as s:
        lat = np.where(np.isfinite(s.read(1)), s.read(1), 0) > 0
    dist_lat = distance_transform_edt(~lat)
    uncovered = footprint & (dist_lat > RADIUS)

    # --- lattice gate for candidates and the nine focus bests -------------
    summary = json.loads((REPO / "evidence/focus_sites_summary.json").read_text())
    subjects: list[tuple[str, bytes]] = []
    for s_ in summary["sites"]:
        m = URL_RE.match(s_["artifact_url"])
        data = extract_member(fetch_tarball(m.group(1), m.group(2), m.group(3), args.cache), m.group(4))
        subjects.append((s_["site"], data))
    for rel in [
        "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-zeros.tif",
        "docs/downloads/gemsdoesass2-sparse-blind-conduit-22163-20261029T000534Z-cc522684-nan.tif",
        "docs/downloads/gemsdoesass2-xghf-dualhorizon-aniso-b2-37654-20261027T131341Z-e7996841-zeros.tif",
    ]:
        subjects.append((Path(rel).name, (REPO / rel).read_bytes()))

    gate_rows = []
    for label, data in subjects:
        dots = dots_from(data, footprint)
        n = int(dots.sum())
        ov = float((dist_lat[dots] <= RADIUS).mean()) if n else None
        gate_rows.append({
            "subject": label,
            "dots": n,
            "lattice_overlap_3px": round(ov, 6) if ov is not None else None,
            "dots_on_lattice_uncovered_cells": int((dots & uncovered).sum()),
            "lattice_gate_pass_le_0_70": (ov is not None and ov <= 0.70),
        })

    # --- lineage: GEMSDOE32 vs GEMSDOE25 vs catalogue --------------------
    d25 = dots_from(dict(subjects)["GEMSDOE25"], footprint)
    d32 = dots_from(dict(subjects)["GEMSDOE32"], footprint)
    removed = d25 & ~d32
    lineage = {
        "gemsdoe25_dots": int(d25.sum()),
        "gemsdoe32_dots": int(d32.sum()),
        "gemsdoe32_pixels_not_in_gemsdoe25": int((d32 & ~d25).sum()),
        "removed_dots": int(removed.sum()),
        "removed_all_within_2px_of_catalogue": bool((dist_cat[removed] <= 2).all()),
        "gemsdoe25_minus_catalogue_2px_equals_gemsdoe32": bool(((d25 & (dist_cat > 2)) == d32).all()),
    }

    # --- marginal-dot identity (checked numerically) ----------------------
    rng = np.random.default_rng(1)
    violations = 0
    trials = 20000
    for _ in range(trials):
        tp, fp, fn = rng.uniform(1, 100, 3)
        s = tp + ALPHA * fp + BETA * fn
        dti0 = tp / s
        q = rng.uniform()
        dti_removed = (tp - q) / (s - ALPHA)  # remove a dot: TP-=q, FP-=1-q, FN+=q (alpha+beta=1)
        improves = dti_removed > dti0
        if improves != (q < ALPHA * dti0):
            violations += 1
    identity = {
        "statement": "For alpha+beta=1, removing a dot with expected hit probability q raises DTI iff q < alpha*DTI.",
        "trials": trials, "violations": violations,
        "threshold_at_user_reported_0_2600": round(ALPHA * 0.2600, 4),
        "threshold_at_user_reported_0_2778": round(ALPHA * 0.2778, 4),
    }

    receipt = {
        "schema": "gate-and-lineage-recheck-v1",
        "lattice_registry_raster": {
            "source": f"https://github.com/{owner}/{repo}/blob/{sha}/{LATTICE_PIN['path']}",
            "sha256": lat_sha, "sha256_pin_matches": lat_sha == LATTICE_PIN["sha256"],
            "positive_pixels_in_footprint": int((lat & footprint).sum()),
        },
        "footprint_cells": int(footprint.sum()),
        "footprint_cells_uncovered_by_lattice_3px": int(uncovered.sum()),
        "uncovered_cells_median_distance_to_footprint_edge_cells": float(
            np.median(distance_transform_edt(footprint)[uncovered])),
        "lattice_rule": "FAIL if >70% of dots within 3 px of lattice; literal rule from the protocol",
        "lattice_gate_rows": gate_rows,
        "lineage_0_2778": lineage,
        "marginal_identity": identity,
        "scores": "none computed; user-reported values are labels only",
    }
    OUT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    for row in gate_rows:
        print(f"{row['subject'][:64]:64s} dots={row['dots']:6d} lattice_ov={row['lattice_overlap_3px']} "
              f"pass={row['lattice_gate_pass_le_0_70']}")
    print("lineage:", lineage)
    print("identity violations:", violations, "of", trials)
    print("wrote", OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
