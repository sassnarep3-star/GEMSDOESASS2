"""Reproducible byte and geometry audit; no models and no submissions are made."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

from .fetch import ROOT, CACHE, sha256, verify_template


def _load_shared():
    # Imported from the separately retrieved, unmodified upstream template.
    path = verify_template()
    sys.path.insert(0, str(path))
    from gems57 import uniqueness
    if Path(uniqueness.__file__).resolve() != (path / 'gems57/uniqueness.py').resolve():
        raise RuntimeError('a different gems57 package was imported; refusing to audit')
    return uniqueness


def _load_one(item, footprint, expected):
    path = CACHE / 'inputs' / f'{item["id"]}.tif'
    if not path.is_file() or sha256(path) != item['sha256']:
        raise ValueError(f'missing or hash-mismatched input {item["id"]}')
    with rasterio.open(path) as ds:
        if (ds.shape, ds.crs, ds.transform) != expected or ds.count != 1:
            raise ValueError(f'{item["id"]}: grid or band mismatch')
        if len(ds.files) != 1:
            raise ValueError(f'{item["id"]}: unpinned external dataset sidecar')
        arr = ds.read(1)
        mask = ds.read_masks(1)
        finite = np.isfinite(arr)
        inside = arr[footprint]
        inside_finite = np.isfinite(inside)
        valid = inside[inside_finite]
        metadata = {
            'grid_matches_owner_mirror': True,
            'bands': ds.count,
            'dtype': ds.dtypes[0],
            'nodata': 'nan' if ds.nodata is not None and np.isnan(ds.nodata) else ds.nodata,
            'nan_or_inf_inside': int((~inside_finite).sum()),
            'min_inside': float(valid.min()) if valid.size else None,
            'max_inside': float(valid.max()) if valid.size else None,
            'all_inside_finite_and_in_0_1': bool(valid.size == inside.size and valid.size > 0
                and valid.min() >= 0 and valid.max() <= 1),
            'inside_marked_invalid_by_dataset_mask': int(((mask == 0) & footprint).sum()),
            'raw_nonfinite_total': int((~finite).sum()),
            'outside_marked_invalid_by_dataset_mask': int(((mask == 0) & ~footprint).sum()),
            'outside_cells': int((~footprint).sum()),
        }
    # The literal shared-template convention is positive finite pixels, not a
    # >=0.5 threshold. Comparisons are made only in the common footprint.
    return (np.isfinite(arr) & (arr > 0) & footprint), metadata


def lattice_budget_bound(uncovered: int, count: int) -> dict:
    """Lower-bound overlap; equality with 70% is allowed by the strict rule."""
    if (isinstance(uncovered, bool) or isinstance(count, bool)
            or not isinstance(uncovered, int) or not isinstance(count, int)
            or uncovered < 0 or count <= 0):
        raise ValueError('uncovered must be a nonnegative integer and count a positive integer')
    return {
        'dots': count,
        'minimum_possible_overlap': max(0, count - uncovered) / count,
        'first_n_with_forced_strict_stop': (10 * uncovered) // 3 + 1,
        'derivation': 'At most U dots can lie outside the halo; (N-U)/N > 0.70 iff 3N > 10U.',
    }


def run_audit():
    manifest = json.loads((ROOT / 'data/inputs.json').read_text())
    by_id = {row['id']: row for row in manifest['items']}
    if len(by_id) != len(manifest['items']):
        raise ValueError('duplicate input id')
    for item in manifest['items']:
        p = CACHE / 'inputs' / f'{item["id"]}.tif'
        if not p.is_file() or sha256(p) != item['sha256']:
            raise ValueError(f'{item["id"]}: input missing or SHA-256 mismatch')
    uniqueness = _load_shared()
    registry_manifest = json.loads((ROOT / 'data/registry.json').read_text())
    registry_path = CACHE / 'registry/registry_refreshed.json'
    if not registry_path.is_file() or sha256(registry_path) != registry_manifest['sha256']:
        raise ValueError('historical registry snapshot missing or hash-mismatched; run scripts/fetch_inputs.py --inputs-only')
    registry = json.loads(registry_path.read_text())
    membership = {}
    for ident in ('lattice', 'dense_surface'):
        item = by_id[ident]
        source = f'{item["repo"].split("/")[-1]}:{item["path"]}'
        matches = [r for r in registry['rasters'] if r.get('sha256') == item['sha256']
                   and source in r.get('sources', [])]
        if len(matches) != 1:
            raise ValueError(f'{ident}: exact hash and source absent or ambiguous in pinned historical registry')
        membership[ident] = {'sha256': item['sha256'], 'source': source}
    registry_snapshot = {
        'source': f'https://github.com/{registry_manifest["repo"]}/blob/{registry_manifest["ref"]}/{registry_manifest["path"]}',
        'sha256': registry_manifest['sha256'], 'generated_utc': registry.get('generated_utc'),
        'rasters_listed': len(registry['rasters']),
        'witness_membership': membership,
        'scope': 'Historical accessible-owner snapshot, not a complete current or organizer registry.',
    }
    sample = CACHE / 'inputs/sample.tif'
    with rasterio.open(sample) as ds:
        if ds.count != 1 or ds.crs is None:
            raise ValueError('invalid reference raster')
        if len(ds.files) != 1:
            raise ValueError('reference has an unpinned external dataset sidecar')
        sample_values = ds.read(1)
        footprint = np.isfinite(sample_values) & (ds.read_masks(1) != 0)
        expected = (ds.shape, ds.crs, ds.transform)
        reference = {
            'sha256': by_id['sample']['sha256'], 'authority': 'owner mirror; official origin unverified',
            'height': ds.height, 'width': ds.width, 'crs': str(ds.crs),
            'transform': list(ds.transform)[:6], 'footprint_cells': int(footprint.sum()),
            'finite_positive_cells_in_sample': int((footprint & (sample_values > 0)).sum()),
            'nodata': 'nan' if ds.nodata is not None and np.isnan(ds.nodata) else ds.nodata,
        }
    with rasterio.open(CACHE / 'inputs/labels.tif') as ds:
        if (ds.shape, ds.crs, ds.transform) != expected or ds.count != 1:
            raise ValueError('labels grid differs from reference')
        if len(ds.files) != 1:
            raise ValueError('labels have an unpinned external dataset sidecar')
        raw_labels = ds.read(1)
        catalogue = np.isfinite(raw_labels) & (raw_labels > 0) & (ds.read_masks(1) != 0) & footprint
    reference['catalogue_positive_cells'] = int(catalogue.sum())
    reference['sample_positive_on_catalogue'] = int(((sample_values > 0) & catalogue).sum())
    del raw_labels, sample_values

    # The template's canonical diagnostic is used unchanged.  A universal
    # witness suffices for STOP even if the complete registry is unavailable.
    certificates = {}
    for ident in ('lattice', 'dense_surface'):
        path = CACHE / 'inputs' / f'{ident}.tif'
        with rasterio.open(path) as witness:
            if len(witness.files) != 1:
                raise ValueError(f'{ident}: unpinned external dataset sidecar')
        cert = uniqueness.saturation_certificate(path, footprint, expected_grid=expected)
        cert['witness_file'] = by_id[ident]['path']
        cert['source_repo'] = by_id[ident]['repo']
        cert['source_ref'] = by_id[ident]['ref']
        certificates[ident] = cert

    # A strict > 70% rule allows equality.  If at most U cells are outside a
    # registry halo, any N-dot set has >= max(0, N-U)/N overlap.
    uncovered = certificates['lattice']['uncovered_allowed_pixels']
    count = 37654  # Historical standard budget only; not assumed for every future run.
    certificates['lattice']['budget_example'] = lattice_budget_bound(uncovered, count)

    history = [r for r in manifest['items'] if r['kind'] == 'focus_history']
    candidates = [r for r in manifest['items'] if r['kind'] == 'contradictory_candidate']
    masks, metadata = {}, {}
    for item in history + candidates:
        masks[item['id']], metadata[item['id']] = _load_one(item, footprint, expected)
    # Precompute each shared-template Euclidean 3-px halo once.
    halos = {item['id']: uniqueness._near(masks[item['id']]) for item in history}
    lattice_path = CACHE / 'inputs/lattice.tif'
    with rasterio.open(lattice_path) as ds:
        la = ds.read(1)
    lattice_halo = uniqueness._near(np.isfinite(la) & (la > 0) & footprint)
    del la

    def fraction(mask, halo):
        n = int(mask.sum())
        return float(halo[mask].mean()) if n else None

    rows = []
    for item in history:
        ident = item['id']
        mask = masks[ident]
        comparisons = {other['id']: fraction(mask, halos[other['id']])
                       for other in history if other['id'] != ident}
        measured = {k: v for k, v in comparisons.items() if v is not None}
        worst_id = max(measured, key=measured.get) if measured else None
        rows.append({
            'site': item['repo'].split('/')[-1], 'id': ident,
            'filename': Path(item['path']).name, 'sha256': item['sha256'],
            'source': f'https://github.com/{item["repo"]}/blob/{item["ref"]}/{item["path"]}',
            'score_evidence': item['score_evidence'], 'owner_reported_score': item['owner_reported_score'],
            'estimated_leaderboard_score': None,
            'positive_pixels': int(mask.sum()), 'metadata': metadata[ident],
            'worst_of_other_eight': worst_id, 'worst_overlap_3px': measured.get(worst_id),
            'overlaps_3px': comparisons,
            'exact_same_support_as': [other['id'] for other in history
                if other['id'] != ident and np.array_equal(mask, masks[other['id']])],
            'overlap_lattice': fraction(mask, lattice_halo),
            'unique_among_other_eight': bool(worst_id and measured[worst_id] <= .70),
            'action': 'ALREADY REPORTED AS SUBMITTED — DO NOT RESUBMIT',
        })
    candidate_rows = []
    for item in candidates:
        mask = masks[item['id']]
        candidate_rows.append({
            'id': item['id'], 'filename': Path(item['path']).name, 'sha256': item['sha256'],
            'source': f'https://github.com/{item["repo"]}/blob/{item["ref"]}/{item["path"]}',
            'positive_pixels': int(mask.sum()), 'metadata': metadata[item['id']],
            'overlap_lattice': fraction(mask, lattice_halo),
            # If the witness covers all footprint cells this is exactly 1.0 for
            # every nonempty candidate; no optimistic unmeasured inference.
            'overlap_dense_surface': 1.0 if certificates['dense_surface']['universal_overlap_blocker']
                and mask.any() else None,
            'surface_comparison': None,
            'decision': 'NEGATIVE — literal registry stop; not authorized to submit',
        })

    h33, b1, anderson = masks['gemsdoe32'], masks['gemsdoe31'], masks['gemsdoe36']
    relations = {
        'b2_outside_b1': int((h33 & ~b1).sum()),
        'b1_missing_from_b2': int((b1 & ~h33).sum()),
        'b2_missing_from_anderson': int((h33 & ~anderson).sum()),
        'anderson_extra_over_b2': int((anderson & ~h33).sum()),
        'gems25_gems30_support_equal': bool(np.array_equal(masks['gemsdoe25'], masks['gemsdoe30'])),
    }
    return {
        'schema': 'gems-portfolio-audit-v1', 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Nine selected owner-mirrored historical rasters, two owner candidates and two registry witnesses; NOT a complete registry or an organizer receipt.',
        'experiments_run': 0, 'competition_slots_used': 0, 'reference': reference,
        'registry_snapshot': registry_snapshot, 'certificates': certificates, 'focus_history': rows,
        'candidate_counterexamples': candidate_rows, 'nested_support': relations,
        'current_candidate': None, 'leaderboard_estimate': None, 'verdict': 'negative',
        'limitations': ['No explicitly assigned single-method lane.',
            'Shared prepared feature stack absent.', 'Full current registry and pre-placement surfaces unavailable.',
            'No new feature canaries, buffered holdout, CI, or new TIFF were produced.',
            'No authenticated organizer score receipt, quota or selector approval.'],
    }
