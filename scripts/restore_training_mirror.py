#!/usr/bin/env python3
"""Assemble a hash-pinned public owner mirror of the raw multiband input.

This does not build or replace the shared prepared feature cache. Never commits
or uploads the large data. Official provenance remains unverified.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from gems_audit.fetch import ROOT, CACHE, sha256


def restore(manifest, destination):
    expected = manifest['sha256']
    if destination.is_file() and sha256(destination) == expected:
        return 'cached'
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.training-', suffix='.partial', dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'wb') as output:
            for number, part in enumerate(manifest['parts'], 1):
                print(f'Downloading part {number}/{len(manifest["parts"])}', flush=True)
                endpoint = f'repos/{manifest["repo"]}/contents/{quote(part, safe="/")}?ref={manifest["ref"]}'
                subprocess.run(['gh', 'api', endpoint, '-H', 'Accept: application/vnd.github.raw'],
                               stdout=output, check=True)
        if temporary.stat().st_size != manifest['bytes'] or sha256(temporary) != expected:
            raise ValueError('Assembled owner-mirror training raster failed size or SHA-256 verification')
        os.replace(temporary, destination)
        return 'restored'
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=CACHE / 'inputs/training_features.tif')
    args = parser.parse_args()
    man = json.loads((ROOT / 'data/training-mirror.json').read_text())
    state = restore(man, args.destination)
    print(f'{state}: {args.destination} sha256={man["sha256"]}')
    print('Raw owner mirror only: shared prepared feature stack is still required.')


if __name__ == '__main__':
    main()
