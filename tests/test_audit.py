import json
from pathlib import Path

import numpy as np
import pytest

from gems_audit.audit import lattice_budget_bound


def test_lattice_bound_uses_strict_threshold_and_handles_small_sets():
    # Three uncovered cells allow exactly 70% overlap at N=10; it is NOT >70%.
    assert lattice_budget_bound(3, 10)['minimum_possible_overlap'] == pytest.approx(.7)
    assert lattice_budget_bound(3, 10)['first_n_with_forced_strict_stop'] == 11
    assert lattice_budget_bound(3, 11)['minimum_possible_overlap'] > .7
    assert lattice_budget_bound(20, 5)['minimum_possible_overlap'] == 0
    bound = lattice_budget_bound(6649, 37654)
    assert bound['first_n_with_forced_strict_stop'] == 22164
    assert bound['minimum_possible_overlap'] == pytest.approx(31005 / 37654)


@pytest.mark.parametrize('u,n', [(-1, 2), (1, 0), (True, 2), (1, 3.5)])
def test_lattice_bound_rejects_invalid_inputs(u, n):
    with pytest.raises(ValueError):
        lattice_budget_bound(u, n)


def test_evidence_is_negative_and_focus_claims_are_unverified():
    root = Path(__file__).resolve().parents[1]
    audit = json.loads((root / 'evidence/portfolio-audit.json').read_text())
    card = json.loads((root / 'evidence/run-card.json').read_text())
    assert len(audit['focus_history']) == 9
    assert all(not row['unique_among_other_eight'] for row in audit['focus_history'])
    assert all(row['estimated_leaderboard_score'] is None for row in audit['focus_history'])
    assert all('unverified' in row['score_evidence'] for row in audit['focus_history'])
    assert audit['certificates']['dense_surface']['universal_overlap_blocker']
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['raster_sha256'] is None and card['holdout_dti']['value'] is None
    assert card['submission_slots_used'] == 0


def test_sample_nesting_is_recorded_without_score_inference():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / 'evidence/portfolio-audit.json').read_text())
    result = data['nested_support']
    assert result == {'b2_outside_b1': 0, 'b1_missing_from_b2': 2545,
                      'b2_missing_from_anderson': 0, 'anderson_extra_over_b2': 1200,
                      'gems25_gems30_support_equal': True}
