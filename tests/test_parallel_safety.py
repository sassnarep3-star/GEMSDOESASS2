"""Regression checks for concurrent research artifacts; no submission approval."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio

from scripts.audit_snapshot import sha256_file

ROOT = Path(__file__).resolve().parents[1]
LEGACY = [
    'generate_submission.py', 'build_submission.py', 'run_pipeline.py',
    'experiments.py', 'check_uniqueness.py', 'check_uniqueness_sgmc.py',
    'finalize_card.py', 'build_site.py', 'sgmc_calibration.py',
]


@pytest.mark.parametrize('script', LEGACY)
def test_legacy_entry_points_fail_closed(script):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert 'DO NOT SUBMIT' in result.stderr


def test_parallel_saved_bytes_match_audit_and_fail_lattice():
    audit = json.loads((ROOT / 'docs/data/audit.json').read_text())
    witnesses = {w['id']: w for w in audit['existing_candidate_witnesses']}
    expected = {
        'parallel_ttc_zeros': (37637, 37654), 'parallel_ttc_nan': (37637, 37654),
        'parallel_altedge': (43792, 44090), 'parallel_scu_zeros': (36945, 37000),
        'parallel_scu_nan': (36945, 37000),
    }
    for key, (overlap, dots) in expected.items():
        w = witnesses[key]
        assert (w['dots_within_3px'], w['candidate_dots']) == (overlap, dots)
        assert w['fails_literal_overlap_rule'] and w['fraction'] > .70
        assert sha256_file(ROOT / w['path']) == w['sha256']
    for first, second in [('parallel_ttc_zeros', 'parallel_ttc_nan'),
                          ('parallel_scu_zeros', 'parallel_scu_nan')]:
        with rasterio.open(ROOT / witnesses[first]['path']) as a, rasterio.open(ROOT / witnesses[second]['path']) as b:
            assert np.array_equal(a.read(1) == 1, b.read(1) == 1)


def test_parallel_format_reports_and_withdrawn_cards():
    for name in ['altedge', 'ttc-zeros', 'ttc-nan', 'scu-zeros', 'scu-nan']:
        r = json.loads((ROOT / f'docs/data/format-parallel-{name}.json').read_text())
        assert r['checks']['inside_unmasked_finite_in_0_1']
        assert r['checks']['competition_crs_epsg32611']
        assert r['checks']['shape_match'] and r['checks']['transform_match']
        assert r['strict_local_format_pass'] is False
        assert r['organizer_accepted'] is None and r['ok_to_submit'] is False
    for p in ['evidence/ttc_run_card_d8f85365.json', 'evidence/run_card.json', 'registry/run_card.json']:
        c = json.loads((ROOT / p).read_text())
        assert c['verdict'] == 'negative' and c['ok_to_submit'] is False
    ttc = json.loads((ROOT / 'evidence/ttc_run_card_d8f85365.json').read_text())
    assert ttc['holdout_DTI'] is None
    scu = json.loads((ROOT / 'evidence/run_card.json').read_text())
    assert scu['estimated_live_score']['point'] is None
    assert scu['uniqueness']['all_pass'] is False


def test_research_archives_contain_one_matching_tiff():
    from hashlib import sha256
    from zipfile import ZipFile
    archives = list((ROOT / 'docs/downloads').glob('*.zip'))
    assert len(archives) == 5
    for archive in archives:
        with ZipFile(archive) as z:
            names = z.namelist()
            assert len(names) == 1 and names[0].lower().endswith('.tif')
            assert sha256(z.read(names[0])).digest() == sha256((archive.parent / names[0]).read_bytes()).digest()


@pytest.mark.parametrize('entry, positional', [
    ('validate.py', False), ('check_submission.py', False), ('validate_submission.py', True),
])
def test_validator_compatibility_does_not_approve_parallel_tiff(entry, positional):
    candidate = ROOT / 'docs/downloads/gemsdoesass2-scu1-scarpcorridor-uth-37000-20261027T120000Z-zeros.tif'
    sample = ROOT / 'data/bridge/sample_submission.tif'
    command = [sys.executable, str(ROOT / 'scripts' / entry), str(candidate)]
    command += [str(sample)] if positional else ['--sample', str(sample)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode == 2, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt['checks']['whole_array_finite_in_0_1']
    assert not receipt['strict_local_format_pass'] and not receipt['ok_to_submit']
