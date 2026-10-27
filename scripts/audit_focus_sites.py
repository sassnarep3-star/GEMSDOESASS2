#!/usr/bin/env python3
"""Audit nine historical focus-site artifacts for exact and lane-level duplication."""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoesass2.io import assert_same_grid, sha256_file, template_footprint  # noqa: E402
from gemsdoesass2.registry import DOT_OVERLAP_LIMIT, RANK_CORRELATION_LIMIT, load_manifest, rank_correlation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--registry-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=ROOT / "registry" / "focus_registry.json")
    parser.add_argument("--labels", type=Path, default=None, help="Optional public catalogue proxy for B2/D2.8 relation audit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    footprint, _, _ = template_footprint(args.template)
    entries: list[dict] = []
    for entry in manifest["entries"]:
        path = args.registry_dir / entry["local_filename"]
        if not path.is_file() or sha256_file(path) != entry["sha256"]:
            raise SystemExit(f"Missing or mismatched registry entry: {entry['id']}")
        assert_same_grid(args.template, path, left_name="template", right_name=entry["id"])
        with rasterio.open(path) as source:
            values = source.read(1).astype(np.float32)
        mask = (np.nan_to_num(values, nan=0.0) > 0.0) & footprint
        entries.append({**entry, "values": values, "mask": mask, "dot_count": int(mask.sum())})

    pairs: list[dict] = []
    failed_by_id: dict[str, list[str]] = {entry["id"]: [] for entry in entries}
    for left, right in itertools.combinations(entries, 2):
        left_mask, right_mask = left["mask"], right["mask"]
        corr, corr_mode, n_cells = rank_correlation(left["values"], right["values"], footprint)
        right_distance = distance_transform_edt(~right_mask)
        left_distance = distance_transform_edt(~left_mask)
        left_overlap = float((left_mask & (right_distance <= 3.0)).sum() / left_mask.sum())
        right_overlap = float((right_mask & (left_distance <= 3.0)).sum() / right_mask.sum())
        exact = bool(np.array_equal(left_mask, right_mask))
        lane_duplicate = corr > RANK_CORRELATION_LIMIT or left_overlap > DOT_OVERLAP_LIMIT or right_overlap > DOT_OVERLAP_LIMIT
        if lane_duplicate:
            failed_by_id[left["id"]].append(right["id"])
            failed_by_id[right["id"]].append(left["id"])
        pairs.append(
            {
                "left": left["id"],
                "right": right["id"],
                "exact_binary_mask_duplicate": exact,
                "abs_rank_correlation": corr,
                "rank_correlation_mode": corr_mode,
                "comparison_pixels": n_cells,
                "left_directed_dot_overlap_within_3px": left_overlap,
                "right_directed_dot_overlap_within_3px": right_overlap,
                "fails_literal_lane_rule": lane_duplicate,
            }
        )
    relation: dict[str, object] = {}
    by_id = {entry["id"]: entry for entry in entries}
    d28 = by_id.get("GEMSDOE25-D2.8")
    b2 = by_id.get("GEMSDOE32-H33-B2")
    if d28 and b2:
        removed = d28["mask"] & ~b2["mask"]
        relation = {
            "b2_is_exact_binary_subset_of_d28": bool(not (b2["mask"] & ~d28["mask"]).any()),
            "d28_dot_count": int(d28["mask"].sum()),
            "b2_dot_count": int(b2["mask"].sum()),
            "d28_dots_removed_in_b2": int(removed.sum()),
        }
        if args.labels:
            assert_same_grid(args.template, args.labels, left_name="template", right_name="labels")
            with rasterio.open(args.labels) as source:
                catalogue = source.read(1) > 0
            distances = distance_transform_edt(~catalogue)
            # Euclidean distance also has diagonal values (sqrt(2)), so report
            # protocol-relevant bins rather than falsely calling every removed
            # cell "exactly two pixels" away.
            relation["removed_dots_distance_le_1px"] = int((removed & (distances <= 1.0)).sum())
            relation["removed_dots_distance_gt_1_le_2px"] = int((removed & (distances > 1.0) & (distances <= 2.0)).sum())
            relation["removed_dots_distance_gt_2px"] = int(removed.sum() - relation["removed_dots_distance_le_1px"] - relation["removed_dots_distance_gt_1_le_2px"])
    result = {
        "schema": "gemsdoesass2-focus-site-audit-v1",
        "scope": "Pinned nine-site public artifacts. Scores remain OWNER-REPORTED historical claims; audit does not verify submissions or leaderboard receipts.",
        "limits": {"abs_rank_correlation": RANK_CORRELATION_LIMIT, "directed_dot_overlap_within_3px": DOT_OVERLAP_LIMIT},
        "sites": [
            {
                "id": entry["id"],
                "site": entry["site"],
                "file": entry["historical_file"],
                "sha256": entry["sha256"],
                "dot_count": entry["dot_count"],
                "historical_claim": entry["historical_claim"],
                "literal_nine_site_lane_pass": not failed_by_id[entry["id"]],
                "conflicts": failed_by_id[entry["id"]],
            }
            for entry in entries
        ],
        "pairs": pairs,
        "b2_d28_relationship": relation,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
