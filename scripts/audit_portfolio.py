#!/usr/bin/env python3
"""Audit pinned public bytes. This performs no geological experiment or upload."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.audit import run_audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('evidence/portfolio-audit.json'))
    args = parser.parse_args()
    result = run_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Wrote', args.output)
    print('Witnesses:', json.dumps(result['certificates'], indent=2))
    print('Historical masks:', json.dumps(result['nested_support'], indent=2))
    for row in result['candidate_counterexamples']:
        print(row['id'], 'lattice overlap=', row['overlap_lattice'], 'dense overlap=', row['overlap_dense_surface'])
    print('Decision: NEGATIVE — no current candidate; no slot used')


if __name__ == '__main__':
    main()
