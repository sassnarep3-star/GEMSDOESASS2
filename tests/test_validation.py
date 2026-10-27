from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems_audit.validation import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / '.cache/template/src/gems57/gates.py').exists(),
                                reason='run scripts/fetch_inputs.py --template-only')


def write_tif(path, arr, *, nodata=None, mask=None, transform=None):
    transform = transform or from_origin(0, 500, 100, 100)
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=True):
        with rasterio.open(path, 'w', driver='GTiff', width=arr.shape[1], height=arr.shape[0],
                           count=1, dtype='float32', crs='EPSG:32611', transform=transform,
                           nodata=nodata) as out:
            out.write(arr.astype('float32'), 1)
            if mask is not None:
                out.write_mask(mask.astype('uint8') * 255)


def test_reopened_file_checks_null_mask_and_does_not_authorize(tmp_path):
    fp = np.ones((5, 5), bool)
    fp[0, 0] = False
    sample_arr = np.zeros((5, 5), dtype='float32')
    sample_arr[0, 0] = np.nan
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    write_tif(sample, sample_arr, nodata=np.nan)
    pred = np.zeros((5, 5), dtype='float32')
    pred[2, 2] = 1
    write_tif(candidate, pred, mask=fp)
    result = validate_candidate(candidate, sample)
    assert all(result['checks'].values())
    assert result['outside_footprint_marked_null_or_nan'] is True
    assert result['shared_template_local_format']['ok'] is True
    assert result['weekly_slot_authorized'] is False
    assert result['organizer_acceptance'] == 'unknown'


def test_range_sentinel_and_nan_inside_rejected_without_repair(tmp_path):
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    write_tif(sample, np.zeros((5, 5), dtype='float32'))
    pred = np.zeros((5, 5), dtype='float32')
    pred[1, 1] = -9999
    pred[2, 2] = np.nan
    write_tif(candidate, pred)
    before = candidate.read_bytes()
    result = validate_candidate(candidate, sample)
    assert result['checks']['finite_values_in_0_1'] is False
    assert result['checks']['inside_finite_and_in_0_1'] is False
    assert result['shared_template_local_format']['ok'] is False
    assert candidate.read_bytes() == before


def test_grid_mismatch_does_not_attempt_to_index_wrong_shape(tmp_path):
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    write_tif(sample, np.zeros((5, 5), dtype='float32'))
    write_tif(candidate, np.zeros((3, 3), dtype='float32'))
    result = validate_candidate(candidate, sample)
    assert not result['checks']['shape_matches_reference']
    assert result['outside_footprint_marked_null_or_nan'] is None


def test_reference_finite_nodata_and_candidate_invalid_inside(tmp_path):
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    ref = np.zeros((5, 5), dtype='float32')
    ref[0, 0] = -9999
    write_tif(sample, ref, nodata=-9999)
    mask = np.ones((5, 5), bool)
    mask[0, 0] = False  # correctly outside reference footprint
    mask[2, 2] = False  # INVALID inside, despite its finite zero value
    write_tif(candidate, np.zeros((5, 5), dtype='float32'), mask=mask)
    result = validate_candidate(candidate, sample)
    assert result['reference_footprint_cells'] == 24
    assert result['outside_footprint_marked_null_or_nan'] is True
    assert result['checks']['inside_finite_and_in_0_1'] is True
    assert result['checks']['inside_valid_mask'] is False


def test_external_mask_is_not_silently_treated_as_part_of_single_tiff(tmp_path):
    sample = tmp_path / 'sample.tif'
    candidate = tmp_path / 'candidate.tif'
    write_tif(sample, np.zeros((5, 5), dtype='float32'))
    with rasterio.Env(GDAL_TIFF_INTERNAL_MASK=False):
        with rasterio.open(candidate, 'w', driver='GTiff', width=5, height=5, count=1,
                           dtype='float32', crs='EPSG:32611',
                           transform=from_origin(0, 500, 100, 100)) as out:
            out.write(np.zeros((5, 5), dtype='float32'), 1)
            out.write_mask(np.ones((5, 5), dtype='uint8') * 255)
    result = validate_candidate(candidate, sample)
    assert len(result['candidate_dataset_files']) == 2
    assert result['checks']['standalone_geotiff'] is False


def test_file_change_during_shared_reopen_is_not_a_stable_validation(tmp_path, monkeypatch):
    from gems57 import gates
    sample, candidate = tmp_path / 'sample.tif', tmp_path / 'candidate.tif'
    write_tif(sample, np.zeros((5, 5), dtype='float32'))
    write_tif(candidate, np.zeros((5, 5), dtype='float32'))
    original = gates.format_report
    def change_after_read(*args, **kwargs):
        report = original(*args, **kwargs)
        with candidate.open('ab') as stream:
            stream.write(b'changed after shared reopen')
        return report
    monkeypatch.setattr(gates, 'format_report', change_after_read)
    result = validate_candidate(candidate, sample)
    assert result['checks']['candidate_bytes_stable_during_validation'] is False
    assert result['checks']['reference_files_stable_during_validation'] is True


def test_cli_rejects_finite_masked_inside_and_returns_nonzero(tmp_path):
    import subprocess
    import sys
    sample, candidate = tmp_path / 'sample.tif', tmp_path / 'candidate.tif'
    write_tif(sample, np.zeros((5, 5), dtype='float32'))
    mask = np.ones((5, 5), bool); mask[1, 1] = False
    write_tif(candidate, np.zeros((5, 5), dtype='float32'), mask=mask)
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/check_geotiff.py'), str(candidate),
                           '--sample', str(sample)], text=True, capture_output=True)
    assert proc.returncode == 1
    assert '"inside_valid_mask": false' in proc.stdout
