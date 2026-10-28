#!/usr/bin/env python3
"""Prepare and cache the 36-channel leak-free physical & hydrothermal feature stack.

Writes the memory-mapped array into ``/tmp/sass2_features`` (symlinked from ``.cache/sass2_features``)
and emits an auditable JSON summary at ``data/prepared_manifest.json``.
"""
from __future__ import annotations

# Fail closed: historical source is retained below for forensic review.
import sys as _legacy_sys
_LEGACY_REASON = 'Legacy private feature builder does not use the requested shared feature cache.'
if __name__ == "__main__":
    print(_LEGACY_REASON + " DO NOT SUBMIT.", file=_legacy_sys.stderr)
    raise SystemExit(2)
raise RuntimeError(_LEGACY_REASON)

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems_sass2.features import STATIC_FEATURE_NAMES, build_static_feature_memmap


def main() -> int:
    t0 = time.time()
    tmp_cache = Path("/tmp/sass2_features")
    tmp_cache.mkdir(parents=True, exist_ok=True)
    link = ROOT / ".cache" / "sass2_features"
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.exists():
        link.symlink_to(tmp_cache)

    data_dir = ROOT / ".cache" / "gems_data"
    mm, foot, cat, meta = build_static_feature_memmap(data_dir=data_dir, cache_dir=link, force=True)

    # Verify zero NaN/Inf across all 36 static channels
    col_stats = []
    for j, name in enumerate(STATIC_FEATURE_NAMES):
        col = np.asarray(mm[:, j], dtype=np.float32)
        finite = bool(np.isfinite(col).all())
        if not finite:
            raise RuntimeError(f"Non-finite values detected in static feature {name}")
        col_stats.append({
            "index": j,
            "name": name,
            "mean": round(float(col.mean()), 5),
            "std": round(float(col.std()), 5),
            "min": round(float(col.min()), 4),
            "max": round(float(col.max()), 4),
        })

    out = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "elapsed_sec": round(time.time() - t0, 2),
        "grid_shape": [int(foot.shape[0]), int(foot.shape[1])],
        "footprint_pixels": int(foot.sum()),
        "outside_footprint_pixels": int((~foot).sum()),
        "existing_fault_pixels": int(cat.sum()),
        "n_static_features": len(STATIC_FEATURE_NAMES),
        "catalogue_inputs_used": 0,
        "dist_known_fault_px_stripped": True,
        "all_finite": True,
        "features": col_stats,
    }
    manifest_out = ROOT / "data" / "prepared_manifest.json"
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    manifest_out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[prepare_data] Built {len(STATIC_FEATURE_NAMES)} static features across {int(foot.sum()):,d} footprint pixels in {out['elapsed_sec']:.1f}s -> {manifest_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
