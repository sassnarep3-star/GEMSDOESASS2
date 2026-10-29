#!/usr/bin/env python3
"""Measure how the pinned registry lattice (13GEMSDOE r13) saturates the duplicate rule.

Reads only the hash-pinned cache written by ``scripts/audit_snapshot.py`` (run that first)
and reuses its ``binary_mask`` / ``overlap_fraction`` helpers. It answers two questions:

1. What fraction of each historical top file's dots lie within 3 px of the lattice's dots?
2. Would a *random, geologically meaningless* placement of the same number of dots also
   exceed the literal 70 % limit? (control, seeded, reproducible)

This is a rule audit. It generates no candidate submission, runs no holdout, and uses no
weekly slot. Outputs are measurements against one registry witness, not organizer receipts.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_snapshot import CONFIG, binary_mask, fetch_pinned, overlap_fraction, sha256_file  # noqa: E402

CACHE = ROOT / ".cache" / "priority"
OUT = ROOT / "evidence" / "lattice_saturation_check.json"
LIMIT = 0.70
SEEDS = [0, 1, 2, 3, 4]


def main() -> int:
    config = json.loads(CONFIG.read_text())
    lattice_spec = config["inputs"]["lattice"]
    lattice_path = fetch_pinned(lattice_spec, CACHE / "lattice.tif", fetch=False)
    template_path = fetch_pinned(config["inputs"]["template"], CACHE / "sample_submission.tif", fetch=False)

    with rasterio.open(template_path) as template:
        sample = template.read(1)
        foot = np.isfinite(sample) & (template.read_masks(1) > 0)
        footprint = int(foot.sum())
        lattice = binary_mask(lattice_path, template, foot)
        lattice_near = distance_transform_edt(~lattice) <= 3
        rows = []
        for site in config["sites"]:
            path = fetch_pinned(site, CACHE / (site["site"] + ".tif"), fetch=False)
            mask = binary_mask(path, template, foot)
            res = overlap_fraction(mask, lattice_near)
            rows.append({
                "site": site["site"],
                "reported_id": site["reported_id"],
                "reported_score_user_unverified": site["reported"],
                "sha256": sha256_file(path),
                "dots": res["candidate_dots"],
                "dots_within_3px_of_lattice": res["dots_within_3px"],
                "fraction": round(res["fraction"], 6),
                "fails_literal_70pct_rule": res["fraction"] > LIMIT,
            })

        # Controls: uniformly random dots over the footprint, same counts as the top files.
        footprint_idx = np.flatnonzero(foot.ravel())
        controls = []
        for n in sorted({r["dots"] for r in rows}):
            fracs = []
            for seed in SEEDS:
                rng = np.random.default_rng(seed)
                chosen = rng.choice(footprint_idx, size=n, replace=False)
                m = np.zeros(foot.size, dtype=bool)
                m[chosen] = True
                m = m.reshape(foot.shape)
                fracs.append(overlap_fraction(m, lattice_near)["fraction"])
            controls.append({
                "dots": n,
                "seeds": SEEDS,
                "fraction_min": round(min(fracs), 6),
                "fraction_max": round(max(fracs), 6),
                "all_exceed_70pct": all(f > LIMIT for f in fracs),
            })

    result = {
        "scope": "Rule audit against one pinned registry witness. Not an organizer receipt, "
                 "not a complete registry check, not a holdout score, no candidate generated.",
        "audited_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "lattice": {"path": lattice_spec["path"], "repo": lattice_spec["repo"], "ref": lattice_spec["ref"],
                    "sha256": lattice_spec["sha256"], "positive_pixels": int(lattice.sum())},
        "footprint_pixels": footprint,
        "footprint_pixels_within_3px_of_lattice": int(np.count_nonzero(foot & lattice_near)),
        "footprint_pixels_uncovered": int(np.count_nonzero(foot & ~lattice_near)),
        "limit": LIMIT,
        "historical_top_files": rows,
        "random_placement_controls": controls,
        "new_tiff_created": False,
        "weekly_slots_spent": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.partial")
    try:
        tmp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
        tmp.replace(OUT)
    finally:
        tmp.unlink(missing_ok=True)
    for r in rows:
        print(f"{r['site']:10s} dots={r['dots']:6d} within3px={r['fraction']:.4f} fails={r['fails_literal_70pct_rule']}")
    for c in controls:
        print(f"control dots={c['dots']:6d} fraction {c['fraction_min']:.4f}-{c['fraction_max']:.4f} all_exceed={c['all_exceed_70pct']}")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
