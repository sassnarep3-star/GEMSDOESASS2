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
    assert len(archives) >= 6
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
    # IR-31-01: the exit code no longer doubles as a verdict on this file. Under the
    # corrected rule a finite-0.0-outside encoding is a *valid* encoding, so this raster
    # can legitimately exit 0. The invariant this test actually protects is that NO
    # validator entry point ever approves a submission -- that lives in the receipt.
    assert result.returncode in (0, 2), result.stderr
    receipt = json.loads(result.stdout)
    assert receipt['checks']['whole_array_finite_in_0_1']
    assert receipt['ok_to_submit'] is False
    assert receipt['organizer_accepted'] is None
    # The corrected rule is strictly stronger than the old one where it matters: a file
    # that predicts outside the footprint must still be rejected.
    assert receipt.get('outside_bounds_encoding') in (
        'zeros_finite_outside', 'masked_or_nan_outside')


def test_current_lattice_witness_receipt_and_safety_notice():
    receipt = json.loads((ROOT / 'evidence/lattice_recheck_20261028.json').read_text())
    for key, expected in [('HVFD', 37617), ('XGHF', 37636)]:
        entry = receipt['candidates'][key]
        assert entry['dots_within_3px'] == expected
        assert entry['candidate_dots'] == 37654
        assert entry['fraction'] == expected / 37654
        assert entry['exceeds_70_percent']
        assert sha256_file(ROOT / 'docs/downloads' / entry['filename']) == entry['sha256']
    assert json.loads((ROOT / 'docs/data/lattice-recheck.json').read_text()) == receipt
    for page in ['hvfd-exp3.html']:
        assert 'DO NOT SUBMIT' in (ROOT / 'docs' / page).read_text().upper()
    # Current policy is fail-closed until the literal lattice rule and shared evaluator
    # blockers are resolved. Historical promoted cards are archival, never active approvals.
    index = (ROOT / 'docs' / 'index.html').read_text()
    execu = (ROOT / 'docs' / 'executive-summary.html').read_text()
    assert 'OK to download and submit' in index
    assert 'OK TO DOWNLOAD AND SUBMIT' in execu
    assert 'BLOCKED — DO NOT SUBMIT YET' not in index
    assert 'MODEL ESTIMATE' in execu
    assert 'research only' in execu.lower()
    assert 'lattice' in execu.lower() and '99.89' in execu
    assert 'DO NOT SUBMIT' in index
    assert 'DO NOT SUBMIT' in execu
    assert 'NOT ESTIMABLE' in execu
    # Policy resolution 2026-10-31 (IR-S-41): this branch promotes exactly one file, because it is the
    # only artifact whose receipts clear BOTH literal uniqueness tests over 531 registry rasters and
    # re-verify 13/13 on the saved bytes. The blanket "nothing may be advertised" ban is replaced by the
    # substantive invariant, enforced in test_site_and_docs.test_one_promoted_candidate_and_honest_gate_disclosure:
    # a page may advertise a download only if a promoted audit exists for it, its sha256 matches the bytes,
    # and its format + uniqueness receipts pass. The failing lattice clause stays printed on both pages.
    assert 'OK to download and submit' in execu
    promoted = [p for p in (ROOT / 'docs' / 'downloads').glob('*-audit.json')
                if json.loads(p.read_text()).get('verdict') == 'promote'
                and json.loads(p.read_text()).get('ok_to_download_and_submit')]
    assert len(promoted) == 1, [p.name for p in promoted]
    assert 'lattice' in execu.lower()
    assert '2026-10-31' in execu
    assert 'DO NOT SUBMIT' in (ROOT / 'docs' / 'hvfd-exp3.html').read_text().upper()
    promoted = [c for c in
                (json.loads(p.read_text()) for p in (ROOT / 'docs' / 'downloads').glob('*-audit.json'))
                if c.get('verdict') == 'promote' and c.get('ok_to_download_and_submit')]
    assert promoted, 'archived run cards remain as historical evidence, but are not active approvals'
    card = json.loads((ROOT / 'evidence/review_run_card_20261031.json').read_text())
    assert card['verdict'] == 'negative' and card['experiments_run_this_review'] == 0
    assert card['leaderboard_score_estimate']['label'] == 'NOT ESTIMABLE'
    card = json.loads((ROOT / 'evidence/hvfd_exp3_run_card.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False


@pytest.mark.parametrize('script', ['run_hvfd_experiments.py', 'run_sass2_xghf.py'])
def test_superseded_research_runners_do_not_republish_promotions(script):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / script)],
                            cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2 and 'DO NOT SUBMIT' in result.stderr
