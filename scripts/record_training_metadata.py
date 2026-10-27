#!/usr/bin/env python3
"""Verify and record metadata of the raw owner mirror, not a prepared cache."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import ROOT, CACHE, sha256

man = json.loads((ROOT / 'data/training-mirror.json').read_text())
raw = CACHE / 'inputs/training_features.tif'
sample = CACHE / 'inputs/sample.tif'
if sha256(raw) != man['sha256']:
    raise SystemExit('Training mirror SHA-256 mismatch')
with rasterio.open(raw) as src, rasterio.open(sample) as ref:
    result = {
        'schema': 'gems-raw-mirror-metadata-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'sha256': man['sha256'], 'bytes': raw.stat().st_size,
        'provenance': man['provenance'], 'bands': src.count, 'dtypes': list(src.dtypes),
        'height': src.height, 'width': src.width, 'crs': str(src.crs),
        'transform': list(src.transform)[:6], 'nodata': src.nodata,
        'grid_matches_owner_mirror_sample': (src.shape, src.crs, src.transform) == (ref.shape, ref.crs, ref.transform),
        'band_descriptions_as_found': list(src.descriptions), 'units': list(src.units),
        'prepared_feature_cache': 'not present or verified by this check',
    }
path = ROOT / 'evidence/raw-mirror-metadata.json'
path.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(path)
