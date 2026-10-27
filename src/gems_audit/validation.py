"""Saved-byte preflight. Format checks never authorize an upload."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import rasterio

from .fetch import sha256, verify_template


def validate_candidate(candidate: Path, sample: Path) -> dict:
    """Compare TIFF to supplied grid and inspect both raw values and the GDAL mask.

    Official wording about nulls outside bounds and the portal's handling of
    NaN are not equivalent. Report both separately; never silently repair data.
    """
    candidate, sample = Path(candidate), Path(sample)
    candidate_digest, sample_digest = sha256(candidate), sha256(sample)
    with rasterio.open(sample) as ref:
        if ref.count != 1 or ref.crs is None:
            raise ValueError('reference must have one band and a CRS')
        ref_files = [{'path': name, 'sha256': sha256(Path(name))} for name in ref.files]
        ref_array = ref.read(1)
        # Nodata can be a finite sentinel or an explicit validity mask. Reading
        # only numeric values would incorrectly include masked-out reference cells.
        footprint = np.isfinite(ref_array) & (ref.read_masks(1) != 0)
        ref_grid = (ref.shape, ref.crs, ref.transform)
    if not footprint.any():
        raise ValueError('reference has no finite footprint')
    with rasterio.open(candidate) as ds:
        if ds.count < 1:
            raise ValueError('candidate has no bands')
        data = ds.read(1)
        dataset_mask = ds.read_masks(1)
        aligned = (ds.shape, ds.crs, ds.transform) == ref_grid
        finite = np.isfinite(data)
        values = data[finite]
        candidate_files = list(ds.files)
        checks = {
            'driver_is_geotiff': ds.driver == 'GTiff',
            # An external .msk/.aux sidecar is not included in the TIFF hash or
            # in a single-file upload, so never silently rely on it.
            'standalone_geotiff': len(candidate_files) == 1,
            'one_band': ds.count == 1,
            'float32': ds.dtypes[0] == 'float32',
            'identity_scale_offset': ds.scales[0] == 1 and ds.offsets[0] == 0,
            'crs_matches_reference': ds.crs == ref_grid[1],
            'shape_matches_reference': ds.shape == ref_grid[0],
            'transform_matches_reference': ds.transform == ref_grid[2],
            'epsg_32611': ds.crs is not None and ds.crs.to_epsg() == 32611,
            'finite_values_in_0_1': bool(values.size and values.min() >= 0 and values.max() <= 1),
            'no_infinity_anywhere': bool(not np.isinf(data).any()),
            'no_nan_anywhere': bool(not np.isnan(data).any()),
        }
        outside_marked_null = None
        if aligned:
            inside = data[footprint]
            checks['inside_finite_and_in_0_1'] = bool(np.isfinite(inside).all()
                and (inside >= 0).all() and (inside <= 1).all())
            checks['inside_valid_mask'] = bool((dataset_mask[footprint] != 0).all())
            # Check both pixel value and declared mask; raw finite zeros outside
            # do not on their own establish null status.
            outside_marked_null = bool(np.all((dataset_mask == 0)[~footprint] | np.isnan(data[~footprint])))
        else:
            checks['inside_finite_and_in_0_1'] = False
            checks['inside_valid_mask'] = False
        result = {
            'file': str(candidate), 'sha256': candidate_digest,
            'candidate_dataset_files': candidate_files,
            'sample_sha256': sample_digest, 'reference_dataset_files': ref_files,
            'reference_footprint_cells': int(footprint.sum()),
            'reference_outside_cells': int((~footprint).sum()),
            'grid_authority': 'matches supplied reference only; official origin must be established separately',
            'checks': checks,
            'outside_footprint_marked_null_or_nan': outside_marked_null,
            'outside_note': 'The public spec says null/NaN outside bounds; whether the irregular footprint is intended as bounds and how the portal handles masks are unverified.',
            'finite_min': float(values.min()) if values.size else None,
            'finite_max': float(values.max()) if values.size else None,
            'nan_count': int(np.isnan(data).sum()), 'inf_count': int(np.isinf(data).sum()),
            'scientific_or_novelty_approval': False,
            'weekly_slot_authorized': False,
            'organizer_acceptance': 'unknown',
        }
    # Report the unchanged shared template's stricter all-finite policy too.
    template = verify_template()
    sys.path.insert(0, str(template))
    from gems57 import gates
    if Path(gates.__file__).resolve() != (template / 'gems57/gates.py').resolve():
        raise RuntimeError('a different gems57 package was imported; refusing to validate')
    result['shared_template_local_format'] = gates.format_report(candidate, sample, footprint=footprint)
    # Re-hash after all reads, including the shared validator's reopen, so a
    # changed file cannot be represented as the inspected saved-byte artifact.
    result['checks']['candidate_bytes_stable_during_validation'] = candidate.is_file() and sha256(candidate) == candidate_digest
    result['checks']['reference_files_stable_during_validation'] = sample.is_file() and sha256(sample) == sample_digest and all(
        Path(row['path']).is_file() and sha256(Path(row['path'])) == row['sha256'] for row in ref_files)
    return result
