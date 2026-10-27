#!/usr/bin/env python3
"""Fetch exactly pinned audit inputs and the unchanged shared template into .cache/."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import fetch_inputs, fetch_registry, fetch_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template-only', action='store_true')
    parser.add_argument('--inputs-only', action='store_true')
    args = parser.parse_args()
    if args.template_only and args.inputs_only:
        parser.error('choose at most one of --template-only and --inputs-only')
    if not args.inputs_only:
        fetch_template()
    if not args.template_only:
        fetch_inputs()
        fetch_registry()


if __name__ == '__main__':
    main()
