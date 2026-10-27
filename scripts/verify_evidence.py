#!/usr/bin/env python3
"""Recompute the pinned audit without overwriting the checked-in evidence."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.audit import run_audit
from gems_audit.fetch import ROOT

actual = run_audit()
expected = json.loads((ROOT / 'evidence/portfolio-audit.json').read_text())
for result in (actual, expected):
    result.pop('generated_utc', None)
if actual != expected:
    differing = sorted(key for key in actual.keys() | expected.keys() if actual.get(key) != expected.get(key))
    raise SystemExit('Recomputed evidence differs in: ' + ', '.join(differing))
print('PASS: pinned inputs, witness membership, geometry and all recorded audit values reproduce.')
print('Scope remains selected historical owner files, not the complete current registry or any new candidate.')
