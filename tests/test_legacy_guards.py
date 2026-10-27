import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_concurrent_cards_do_not_claim_current_promotion():
    for file in ('evidence/run_card.json', 'evidence/ttc_run_card_d8f85365.json', 'registry/run_card.json'):
        result = json.loads((ROOT / file).read_text())
        assert result['verdict'] == 'negative' and result['ok_to_submit'] is False
        assert result['independent_registry_recheck']['overlap_registered_lattice_3px'] > .70


def test_legacy_release_scripts_are_disabled_without_mutating_evidence():
    card = ROOT / 'evidence/run_card.json'
    before = card.read_bytes()
    for file in ('scripts/finalize_card.py', 'scripts/run_pipeline.py',
                 'scripts/build_submission.py', 'scripts/generate_submission.py', 'scripts/experiments.py'):
        result = subprocess.run([sys.executable, str(ROOT / file)], cwd=ROOT, capture_output=True, text=True)
        assert result.returncode != 0, file
        assert 'disabled' in result.stderr.lower(), (file, result.stderr)
    assert card.read_bytes() == before
