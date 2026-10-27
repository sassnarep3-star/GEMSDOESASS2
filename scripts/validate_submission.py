#!/usr/bin/env python3
"""Legacy two-positional-argument wrapper for the saved-byte inspector.

Usage: validate_submission.py candidate.tif sample.tif
The caller-supplied sample may be an unverified mirror; this is not approval.
"""
import argparse
import json
from pathlib import Path
from validate_tif import validate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('sample', type=Path)
    args = parser.parse_args()
    result = validate(args.candidate, args.sample)
    print(json.dumps(result, indent=2, allow_nan=False))
    raise SystemExit(0 if result['strict_local_format_pass'] else 2)
