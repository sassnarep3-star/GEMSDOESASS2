#!/usr/bin/env python3
"""Compatibility CLI for the saved-byte validator; never an upload approval."""
import sys
from check_geotiff import main

if __name__ == '__main__':
    # Preserve the legacy FILE SAMPLE positional form while using one validator.
    if len(sys.argv) >= 3 and not sys.argv[2].startswith('-'):
        sys.argv = [sys.argv[0], sys.argv[1], '--sample', sys.argv[2], *sys.argv[3:]]
    raise SystemExit(main())
