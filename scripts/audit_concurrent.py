#!/usr/bin/env python3
"""Recheck concurrent main-session TIFFs against pinned registered witnesses.

This is a byte/geometry audit, not a new geological experiment or an upload.
"""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import CACHE, ROOT, fetch_raw, sha256, verify_template
from gems_audit.validation import validate_candidate


def audit():
    manifest = json.loads((ROOT / 'data/concurrent.json').read_text())
    inputs = {r['id']: r for r in json.loads((ROOT / 'data/inputs.json').read_text())['items']}
    snapshot = json.loads((ROOT / 'data/registry.json').read_text())
    index = CACHE / 'registry/registry_refreshed.json'
    if not index.is_file() or sha256(index) != snapshot['sha256']:
        raise ValueError('missing or altered historical registry; run scripts/fetch_inputs.py --inputs-only')
    registry = json.loads(index.read_text())
    for name in ('sample', 'lattice', 'dense_surface'):
        local = CACHE / f'inputs/{name}.tif'
        if not local.is_file() or sha256(local) != inputs[name]['sha256']:
            raise ValueError(f'missing or altered {name} input')
    for name in ('lattice', 'dense_surface'):
        row = inputs[name]
        source = f'{row["repo"].split("/")[-1]}:{row["path"]}'
        if not any(r['sha256'] == row['sha256'] and source in r['sources'] for r in registry['rasters']):
            raise ValueError(f'{name} not registered in pinned historical snapshot')
    template = verify_template()
    sys.path.insert(0, str(template))
    from gems57 import uniqueness
    if Path(uniqueness.__file__).resolve() != (template / 'gems57/uniqueness.py').resolve():
        raise RuntimeError('unexpected shared-template import')
    sample = CACHE / 'inputs/sample.tif'
    with rasterio.open(sample) as src:
        if len(src.files) != 1:
            raise ValueError('unpinned sample sidecar')
        fp = np.isfinite(src.read(1)) & (src.read_masks(1) != 0)
        grid = (src.shape, src.crs, src.transform)
    with rasterio.open(CACHE / 'inputs/lattice.tif') as src:
        if len(src.files) != 1 or (src.shape, src.crs, src.transform) != grid:
            raise ValueError('lattice grid/sidecar mismatch')
        vals = src.read(1)
        lattice_halo = uniqueness._near(np.isfinite(vals) & (vals > 0) & fp)
    dense_path = CACHE / 'inputs/dense_surface.tif'
    with rasterio.open(dense_path) as ds:
        if len(ds.files) != 1:
            raise ValueError('unpinned witness sidecar')
    dense = uniqueness.saturation_certificate(dense_path, fp, expected_grid=grid)
    if not dense['universal_overlap_blocker']:
        raise ValueError('dense witness no longer proves universal overlap')

    masks, rows = {}, []
    for item in manifest['items']:
        path = CACHE / 'concurrent' / f'{item["id"]}.tif'
        fetch_raw(manifest['repo'], manifest['ref'], item['path'], item['sha256'], path)
        report = validate_candidate(path, sample)
        with rasterio.open(path) as src:
            if len(src.files) != 1 or (src.shape, src.crs, src.transform) != grid or src.count != 1:
                raise ValueError(f'{item["id"]}: grid/sidecar mismatch')
            a = src.read(1)
            mask = np.isfinite(a) & (a > 0) & fp
            if not mask.any():
                raise ValueError(f'{item["id"]}: empty candidate')
            masks[item['id']] = mask
        rows.append({
            'id': item['id'], 'label': item['label'], 'sha256': item['sha256'],
            'source': f'https://github.com/{manifest["repo"]}/blob/{manifest["ref"]}/{item["path"]}',
            'source_card': f'https://github.com/{manifest["repo"]}/blob/{manifest["ref"]}/{item["source_card"]}',
            'positive_pixels': int(mask.sum()),
            'overlap_registered_lattice_3px': float(lattice_halo[mask].mean()),
            'overlap_registered_dense_surface_3px': 1.0,
            'format_checks': report['checks'],
            'shared_template_local_format_ok': report['shared_template_local_format']['ok'],
            'outside_footprint_marked_null_or_nan': report['outside_footprint_marked_null_or_nan'],
            'preplacement_surface_checked': False,
            'full_current_registry_checked': False,
            'decision': 'negative', 'ok_to_submit': False,
        })
    halos = {key: uniqueness._near(mask) for key, mask in masks.items()}
    for row in rows:
        mask = masks[row['id']]
        row['overlap_other_concurrent_dots_3px'] = {
            key: float(halo[mask].mean()) for key, halo in halos.items() if key != row['id']}
    return {
        'schema': 'gems-concurrent-main-audit-v1',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'main_commit_reviewed': manifest['ref'], 'registry_snapshot_sha256': snapshot['sha256'],
        'lattice_sha256': inputs['lattice']['sha256'],
        'dense_witness_sha256': inputs['dense_surface']['sha256'],
        'scope': 'Three prior concurrent-session zero-filled files; no new model, holdout or upload.',
        'candidates': rows, 'experiments_this_audit': 0, 'submission_slots_used_this_audit': 0,
        'verdict': 'negative',
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT / 'evidence/concurrent-main-audit.json')
    p.add_argument('--verify', action='store_true', help='Compare with checked-in evidence without overwriting')
    args = p.parse_args()
    result = audit()
    if args.verify:
        previous = json.loads(args.output.read_text())
        previous.pop('generated_utc', None)
        result.pop('generated_utc', None)
        if previous != result:
            raise SystemExit('Concurrent audit does not reproduce')
        print('PASS: concurrent candidate geometry and format observations reproduce.')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
        print('Wrote', args.output)
    for row in result['candidates']:
        print(row['label'], 'lattice overlap', f"{row['overlap_registered_lattice_3px']*100:.4f}%",
              'dense overlap', f"{row['overlap_registered_dense_surface_3px']*100:.1f}%", 'NEGATIVE')


if __name__ == '__main__':
    main()
