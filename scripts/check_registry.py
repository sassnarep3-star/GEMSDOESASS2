#!/usr/bin/env python3
"""Fail-closed shared-template uniqueness diagnostic; never authorizes upload.

Invoke separately on the pre-placement surface and the final dots. A supplied
registry may only represent accessible owner files; caller must independently
establish its currency, completeness and provenance before any selector step.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import ROOT, CACHE, sha256, verify_template
from gems_audit.validation import validate_candidate


class StopComparison(Exception):
    def __init__(self, reason, checked, row):
        super().__init__(reason)
        self.reason, self.checked, self.row = reason, checked, row


def run(artifact: Path, sample: Path, index: Path, registry_root: Path, phase: str,
        timeout_seconds: int = 7200) -> dict:
    if phase not in ('surface', 'dots') or timeout_seconds <= 0:
        raise ValueError('phase must be surface or dots and timeout positive')
    started = time.monotonic()
    report = validate_candidate(artifact, sample)
    result = {
        'schema': 'gems-registry-check-v1', 'phase': phase,
        'artifact_sha256': report['sha256'], 'reference_sha256': report['sample_sha256'],
        'reference_dataset_files': report['reference_dataset_files'],
        'registry_index_sha256': sha256(index),
        'ok_to_submit': False, 'selector_approval': False,
        'scope': 'A supplied index cannot prove all current/private prior submissions are included.',
    }
    essential = ('driver_is_geotiff', 'standalone_geotiff', 'one_band', 'float32',
                 'identity_scale_offset', 'crs_matches_reference', 'shape_matches_reference',
                 'transform_matches_reference', 'epsg_32611', 'finite_values_in_0_1',
                 'no_infinity_anywhere', 'no_nan_anywhere', 'inside_finite_and_in_0_1',
                 'inside_valid_mask', 'candidate_bytes_stable_during_validation',
                 'reference_files_stable_during_validation')
    if not all(report['checks'][key] for key in essential):
        result.update(verdict='negative', stop_required=True, reason='Candidate format/shared all-finite preflight failed',
                      format_checks=report['checks'])
        return result
    with rasterio.open(sample) as ref, rasterio.open(artifact) as src:
        fp = np.isfinite(ref.read(1)) & (ref.read_masks(1) != 0)
        expected_grid = (ref.shape, ref.crs, ref.transform)
        values = src.read(1)
    if not ((values > 0) & fp).any():
        result.update(verdict='negative', stop_required=True, reason='No positive candidate pixels in reference footprint')
        return result
    if (values[~fp] > 0).any():
        result.update(verdict='negative', stop_required=True, reason='Positive candidate values outside reference footprint')
        return result

    template = verify_template()
    sys.path.insert(0, str(template))
    from gems57 import uniqueness
    if Path(uniqueness.__file__).resolve() != (template / 'gems57/uniqueness.py').resolve():
        raise RuntimeError('a different gems57 package was imported; refusing to compare')
    inventory = json.loads(index.read_text())
    def inputs_stable():
        return (artifact.is_file() and sha256(artifact) == report['sha256']
                and index.is_file() and sha256(index) == result['registry_index_sha256']
                and sample.is_file() and sha256(sample) == report['sample_sha256']
                and all(Path(row['path']).is_file() and sha256(Path(row['path'])) == row['sha256']
                        for row in report['reference_dataset_files']))
    if not inputs_stable():
        result.update(verdict='negative', stop_required=True,
                      reason='Candidate, reference or registry index changed during inspection')
        return result
    if not isinstance(inventory, dict) or not isinstance(inventory.get('rasters'), list):
        raise ValueError('registry must be a full shared-template inventory with a rasters list')
    if not inventory['rasters']:
        result.update(verdict='negative', stop_required=True, reason='Registry index is empty',
                      checked_rasters=0, full_registry_scan=False)
        return result
    for row in inventory['rasters']:
        if (not isinstance(row, dict) or not re.fullmatch(r'[a-f0-9]{64}', str(row.get('sha256', '')))
                or not isinstance(row.get('sources'), list) or not row['sources']
                or not isinstance(row.get('repo_first'), str) or not isinstance(row.get('cache_file'), str)):
            raise ValueError('each registry row must have a SHA-256 pin, source, repository and cache file')

    # Check the hash-pinned positive-everywhere witness first, but only if the
    # supplied inventory actually lists it. One decisive duplicate is sufficient
    # for STOP; it is not a completed registry scan or a candidate rank test.
    witness = json.loads((ROOT / 'data/inputs.json').read_text())
    witness = next(row for row in witness['items'] if row['id'] == 'dense_surface')
    witness_source = f'{witness["repo"].split("/")[-1]}:{witness["path"]}'
    registered = any(r.get('sha256') == witness['sha256'] and witness_source in r.get('sources', [])
                     for r in inventory['rasters'])
    witness_path = CACHE / 'inputs/dense_surface.tif'
    if registered and witness_path.is_file() and sha256(witness_path) == witness['sha256']:
        with rasterio.open(witness_path) as ds:
            if len(ds.files) != 1:
                raise ValueError('registered witness has an unpinned external sidecar')
        certificate = uniqueness.saturation_certificate(witness_path, fp, expected_grid=expected_grid)
        if certificate['universal_overlap_blocker']:
            result.update(verdict='negative', stop_required=True,
                          reason='Literal finite-positive shared support: registered witness covers every footprint pixel',
                          checked_rasters=1, full_registry_scan=False,
                          candidate_overlap_with_witness=1.0, candidate_spearman=None,
                          witness_sha256=witness['sha256'], witness_source=witness_source)
            return result

    # The upstream module resolves relative cache_file paths against its own
    # checkout. Point it at the caller's explicitly selected registry root,
    # without changing the input file, pixel values, thresholds or shared code.
    inventory = dict(inventory)
    inventory['rasters'] = [dict(row) for row in inventory['rasters']]
    for row in inventory['rasters']:
        file = Path(row['cache_file'])
        row['cache_file'] = str(file if file.is_absolute() else (registry_root / file).resolve())

    def stop_on_flag(checked, total, row):
        if 'error' in row:
            raise StopComparison('Registry raster inaccessible or invalid', checked, row)
        if any(row.get(flag, False) for flag in ('duplicate_by_rho', 'duplicate_by_overlap',
                                                'identical_bytes', 'identical_decoded_predictions')):
            raise StopComparison('Duplicate or identical raster found; stop immediately', checked, row)
        if time.monotonic() - started >= timeout_seconds:
            raise StopComparison('Time budget exhausted before complete comparison', checked, row)

    if time.monotonic() - started >= timeout_seconds:
        result.update(verdict='negative', stop_required=True,
                      reason='Time budget exhausted before shared comparison',
                      checked_rasters=0, full_registry_scan=False)
        return result
    try:
        comparison = uniqueness.compare_array_to_registry(values, inventory, fp,
            file_sha256=report['sha256'], expected_grid=expected_grid, progress=stop_on_flag)
    except StopComparison as exc:
        result.update(verdict='negative', stop_required=True, reason=exc.reason,
                      checked_rasters=exc.checked, full_registry_scan=False, stopped_row=exc.row)
        return result
    if not inputs_stable():
        result.update(verdict='negative', stop_required=True,
                      reason='Candidate, reference or registry index changed during comparison',
                      checked_rasters=comparison['registry_rasters_checked'], full_registry_scan=False)
        return result
    # Even a complete accessible-owner scan is not a complete organizer or
    # current-concurrent registry; the selector has independent obligations.
    result.update(verdict='diagnostic-only' if comparison['unique'] else 'negative',
                  stop_required=bool(comparison['stop_required']), comparison=comparison)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifact', type=Path)
    p.add_argument('--phase', required=True, choices=('surface', 'dots'))
    p.add_argument('--sample', required=True, type=Path)
    p.add_argument('--registry-index', required=True, type=Path)
    p.add_argument('--registry-root', required=True, type=Path,
                   help='Root against which relative registry cache_file paths are resolved')
    p.add_argument('--timeout-seconds', type=int, default=7200)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        result = run(args.artifact, args.sample, args.registry_index, args.registry_root, args.phase, args.timeout_seconds)
    except (OSError, ValueError, KeyError, RuntimeError, rasterio.errors.RasterioError) as exc:
        result = {'schema': 'gems-registry-check-v1', 'phase': args.phase,
                  'verdict': 'negative', 'stop_required': True, 'ok_to_submit': False,
                  'selector_approval': False, 'full_registry_scan': False,
                  'reason': f'{type(exc).__name__}: {exc}'}
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text)
    # A diagnostic pass is not release approval. Exit 0 means only this phase
    # did not trigger a STOP within the supplied accessible index.
    return 0 if not result['stop_required'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
