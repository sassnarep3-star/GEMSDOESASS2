#!/usr/bin/env python3
"""Publish the current no-experiment preflight; never treat missing evidence as PASS."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
audit = json.loads((ROOT / 'evidence/portfolio-audit.json').read_text())
parallel = json.loads((ROOT / 'evidence/concurrent-main-audit.json').read_text())
if audit['verdict'] != 'negative' or audit['current_candidate'] is not None:
    raise SystemExit('Unexpected audit state: refusing to overwrite the preflight card')
lattice = audit['certificates']['lattice']
dense = audit['certificates']['dense_surface']
card = {
    'schema': 'gems-run-card-v1',
    'audit_generated_utc': audit['generated_utc'],
    'hypothesis': 'UNTESTED PROPOSAL ONLY: signed multi-scale magnetic texture offsets coupled to a gravity contrast could indicate concealed faults.',
    'mechanism': 'Compare paired cross-strike magnetic textures across scales and test the inferred offset against an independent gravity-side contrast; no implementation or fit was run.',
    'named_non_fault_mimic': 'Unfaulted meandering lithologic contacts, intrusive margins, or magnetic survey-leveling seams.',
    'why_no_hypothesis_run': 'No single method lane was supplied. The ranked ideas are proposals, not an assignment.',
    'experiments_run': 0,
    'experiment_limit': 3,
    'holdout_dti': {'evidence_class': 'HOLDOUT-DTI', 'evaluator_version': None,
                    'withheld_positives': None, 'value': None, 'ci95': None,
                    'reason': 'No candidate or buffered holdout was run.'},
    'leakage_canary': {'status': 'not run; no candidate features'},
    'correlation_overlap_vs_registry': {
        'candidate_surface_spearman': None, 'candidate_final_dot_overlap': None,
        'complete_current_registry_checked': False,
        'lattice_37654_dot_lower_bound': lattice['budget_example']['minimum_possible_overlap'],
        'positive_everywhere_witness_sha256': dense['witness_sha256'],
        'positive_everywhere_literal_overlap_for_nonempty_footprint_candidate': 1.0,
        'scope': 'Witness diagnostics only, not a candidate uniqueness certificate.'},
    'previous_concurrent_candidates': [
        {'name': row['label'], 'sha256': row['sha256'],
         'lattice_overlap': row['overlap_registered_lattice_3px'],
         'literal_dense_surface_overlap': row['overlap_registered_dense_surface_3px'],
         'verdict': 'negative'} for row in parallel['candidates']
    ],
    'raster_sha256': None,
    'validator_output': {'status': 'not run; no new raster', 'no_nan_inside': None,
        'values_in_0_1': None, 'crs_matches': None, 'shape_matches': None, 'transform_matches': None},
    'submission_name': None, 'note': None, 'estimated_leaderboard_score': None,
    'submission_slots_used': 0,
    'selector_approval': False,
    'verdict': 'negative',
    'ok_to_download_new_submission': False,
    'ok_to_submit': False,
    'blockers': audit['limitations'] + [
        'The unchanged shared-template literal support rule makes the positive-everywhere registry surface a universal overlap blocker.',
        'The 5-pixel lattice independently forces >70% overlap at the standard 37,654-dot budget.',
        'Owner-mirrored reference bytes are not organizer-authenticated.',
    ],
}
path = ROOT / 'evidence/run-card.json'
path.write_text(json.dumps(card, indent=2, allow_nan=False) + '\n')
print(path)
