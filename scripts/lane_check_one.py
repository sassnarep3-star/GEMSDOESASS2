#!/usr/bin/env python3
"""One registry raster vs one candidate under the lane rule (exact, dense-aware).

Usage: python scripts/lane_check_one.py <candidate.tif> <registry_blob.tif> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gate_candidate import positives  # noqa: E402


def main() -> int:
    cand_p, ref_p, out_p = sys.argv[1:4]
    with rasterio.open(cand_p) as ds:
        cand = ds.read(1)
    with rasterio.open(ref_p) as ds:
        ref = ds.read(1)
    cp, rp = positives(cand), positives(ref)
    cpts = np.argwhere(cp)
    mask = rp.copy()
    d = distance_transform_edt(~mask)  # exact Euclidean distance to the nearest reference dot
    fwd = float((d[cpts[:, 0], cpts[:, 1]] <= 3.0).mean())
    rec = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "candidate": {"file": Path(cand_p).name, "sha256": hashlib.sha256(Path(cand_p).read_bytes()).hexdigest(), "dots": int(cp.sum())},
        "reference": {"file": Path(ref_p).name, "sha256": hashlib.sha256(Path(ref_p).read_bytes()).hexdigest(), "positives": int(rp.sum()),
                      "note": "registry blob from the nine-repo listing (see registry/gems_registry_manifest.json)"},
        "overlap_3px_fwd": round(fwd, 6), "rule_max": 0.70,
        "lane_duplicate": bool(fwd > 0.70),
    }
    Path(out_p).write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("overlap_3px_fwd", "lane_duplicate")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
