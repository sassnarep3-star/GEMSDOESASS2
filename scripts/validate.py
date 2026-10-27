#!/usr/bin/env python3
"""Compatibility entry point for the conservative saved-byte inspector.

Requires --sample. A local format pass never authorizes submission or proves
organizer acceptance. The previous in-memory/partial checks are in git history.
"""
from validate_tif import main

if __name__ == '__main__':
    raise SystemExit(main())
