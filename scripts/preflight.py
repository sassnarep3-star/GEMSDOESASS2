#!/usr/bin/env python3
"""Fail-closed readiness report; does not train, place dots, write TIFFs or select a slot."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import ROOT, CACHE, sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lane-file', type=Path, help='File containing the explicitly assigned single-method lane')
    parser.add_argument('--feature-cache', type=Path, help='Existing shared prepared feature stack, not raw training TIFF')
    parser.add_argument('--registry-index', type=Path, help='Existing complete, versioned registry inventory')
    args = parser.parse_args()
    template = json.loads((ROOT / 'data/template.json').read_text())
    base = CACHE / 'template/src/gems57'
    template_ok = all((base / row['path']).is_file() and sha256(base / row['path']) == row['sha256']
                      for row in template['files'])
    lane_supplied = bool(args.lane_file and args.lane_file.is_file() and args.lane_file.read_text().strip())
    cache_exists = bool(args.feature_cache and args.feature_cache.is_file())
    registry_exists = bool(args.registry_index and args.registry_index.is_file())
    audit = json.loads((ROOT / 'evidence/portfolio-audit.json').read_text())
    dense = audit['certificates']['dense_surface']
    output = {
        'schema': 'gems-preflight-v1',
        'shared_template_files_hash_match': template_ok,
        'single_lane_text_supplied': lane_supplied,
        'feature_cache_file_exists_not_verified': cache_exists,
        'registry_index_file_exists_not_verified': registry_exists,
        'literal_registered_positive_surface_universal_blocker': dense['universal_overlap_blocker'],
        'witness_sha256': dense['witness_sha256'],
        'candidate_surface_checked': False, 'feature_canaries_checked': False,
        'holdout_evaluated': False, 'final_dot_check': False,
        'saved_tiff_validation': False, 'selector_approval': False,
        'verdict': 'negative', 'ok_to_submit': False,
        'reason': 'File existence is not cache/registry validity; literal witness, missing scientific evidence and separate selector fail closed.',
    }
    print(json.dumps(output, indent=2, allow_nan=False))
    # This command is a diagnostic, not a gate that can approve a submission.
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
