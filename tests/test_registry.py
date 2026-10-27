import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not (ROOT / '.cache/template/src/gems57/uniqueness.py').exists(),
                                reason='run scripts/fetch_inputs.py --template-only')
spec = importlib.util.spec_from_file_location('check_registry', ROOT / 'scripts/check_registry.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def write_tif(path, array):
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, 'w', driver='GTiff', height=array.shape[0], width=array.shape[1],
                       count=1, dtype='float32', crs='EPSG:32611',
                       transform=from_origin(0, 700, 100, 100)) as out:
        out.write(array.astype('float32'), 1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    monkeypatch.setattr(checker, 'ROOT', tmp_path)
    monkeypatch.setattr(checker, 'CACHE', tmp_path / '.cache')
    sample, candidate = tmp_path / 'sample.tif', tmp_path / 'candidate.tif'
    witness = tmp_path / '.cache/inputs/dense_surface.tif'
    write_tif(sample, np.zeros((7, 7), 'float32'))
    field = np.zeros((7, 7), 'float32'); field[0, 0] = 1
    write_tif(candidate, field)
    write_tif(witness, np.full((7, 7), .1, 'float32'))
    man = {'items': [{'id': 'dense_surface', 'repo': 'owner/prior', 'path': 'surface.tif', 'sha256': digest(witness)}]}
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/inputs.json').write_text(json.dumps(man))
    return sample, candidate, witness


def registry(path, records):
    path.write_text(json.dumps({'rasters': records, 'complete_accessible_scan': True, 'errors': []}))


def row(path, source='prior:other.tif'):
    return {'repo_first': 'prior', 'sources': [source], 'cache_file': str(path), 'sha256': digest(path)}


def test_registered_dense_witness_stops_before_any_incomplete_scan(tmp_path, inputs):
    sample, candidate, witness = inputs
    index = tmp_path / 'registry.json'
    registry(index, [row(witness, 'prior:surface.tif')])
    result = checker.run(candidate, sample, index, tmp_path, 'dots')
    assert result['stop_required'] and result['candidate_overlap_with_witness'] == 1
    assert result['full_registry_scan'] is False and result['candidate_spearman'] is None
    assert result['ok_to_submit'] is False


def test_exact_duplicate_stops_shared_scanner_immediately(tmp_path, inputs):
    sample, candidate, _ = inputs
    prior = tmp_path / 'prior.tif'; prior.write_bytes(candidate.read_bytes())
    index = tmp_path / 'registry.json'; registry(index, [row(prior)])
    result = checker.run(candidate, sample, index, tmp_path, 'surface')
    assert result['stop_required'] and result['checked_rasters'] == 1
    assert result['stopped_row']['identical_bytes']


def test_missing_prior_fails_closed_not_unique(tmp_path, inputs):
    sample, candidate, _ = inputs
    prior = tmp_path / 'prior.tif'; write_tif(prior, np.eye(7, dtype='float32'))
    item = row(prior); prior.unlink()
    index = tmp_path / 'registry.json'; registry(index, [item])
    result = checker.run(candidate, sample, index, tmp_path, 'dots')
    assert result['stop_required'] and 'inaccessible' in result['reason']


def test_nonduplicate_is_diagnostic_not_submission_approval(tmp_path, inputs):
    sample, candidate, _ = inputs
    prior = tmp_path / 'prior.tif'
    vals = np.zeros((7, 7), 'float32'); vals[6, 6] = 1
    write_tif(prior, vals)
    index = tmp_path / 'registry.json'; registry(index, [row(prior)])
    result = checker.run(candidate, sample, index, tmp_path, 'dots')
    assert result['verdict'] == 'diagnostic-only' and not result['stop_required']
    assert result['comparison']['unique'] and result['ok_to_submit'] is False


def test_registry_row_without_hash_is_rejected(tmp_path, inputs):
    sample, candidate, witness = inputs
    item = row(witness)
    item.pop('sha256')
    index = tmp_path / 'registry.json'; registry(index, [item])
    with pytest.raises(ValueError, match='SHA-256 pin'):
        checker.run(candidate, sample, index, tmp_path, 'dots')


def test_empty_registry_is_not_a_uniqueness_pass(tmp_path, inputs):
    sample, candidate, _ = inputs
    index = tmp_path / 'registry.json'; registry(index, [])
    result = checker.run(candidate, sample, index, tmp_path, 'dots')
    assert result['stop_required'] and result['verdict'] == 'negative'
