#!/usr/bin/env python3
"""Compatibility entry point: format inspection is not submission approval.

Requires --sample. A local pass is not an organizer receipt or a uniqueness
and slot-selection decision. Previous partial checks are preserved in git history.
"""
from validate_tif import main

if __name__ == '__main__':
    raise SystemExit(main())
