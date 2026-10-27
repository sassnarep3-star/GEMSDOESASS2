"""Retrieve pinned public owner-mirror files; never overwrite an unverified file."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.cache'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_raw(repo: str, ref: str, path: str, expected: str, destination: Path) -> str:
    """Use GitHub's API at an immutable commit and verify SHA-256 before replacing."""
    if destination.is_file() and sha256(destination) == expected:
        return 'cached'
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.fetch-', dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    endpoint = f'repos/{repo}/contents/{quote(path, safe="/")}?ref={quote(ref, safe="")}'
    try:
        with temporary.open('wb') as stream:
            subprocess.run(['gh', 'api', endpoint, '-H', 'Accept: application/vnd.github.raw'],
                           stdout=stream, check=True)
        actual = sha256(temporary)
        if actual != expected:
            raise ValueError(f'{repo}/{path}: SHA-256 mismatch: {actual} != {expected}')
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return 'downloaded'


def fetch_inputs() -> None:
    manifest = json.loads((ROOT / 'data/inputs.json').read_text())
    seen = set()
    for item in manifest['items']:
        ident = item['id']
        if not ident.isidentifier() or ident in seen:
            raise ValueError(f'invalid or duplicate input id: {ident}')
        seen.add(ident)
        dest = CACHE / 'inputs' / f'{ident}.tif'
        state = fetch_raw(item['repo'], item['ref'], item['path'], item['sha256'], dest)
        print(f'{state:10s} {ident:18s} {item["sha256"][:12]}')


def fetch_template() -> None:
    """Download, hash-check, and use the shared template unchanged (not vendored)."""
    man = json.loads((ROOT / 'data/template.json').read_text())
    base = CACHE / 'template' / 'src' / 'gems57'
    for item in man['files']:
        file = Path(item['path'])
        if file.name != item['path'] or file.suffix != '.py':
            raise ValueError('invalid template module name')
        state = fetch_raw(man['repo'], man['ref'], f'{man["root"]}/{file.name}',
                          item['sha256'], base / file.name)
        print(f'{state:10s} template/{file.name} {item["sha256"][:12]}')


def fetch_registry() -> None:
    """Retrieve the historical inventory used to verify witness membership."""
    man = json.loads((ROOT / 'data/registry.json').read_text())
    path = CACHE / 'registry' / 'registry_refreshed.json'
    state = fetch_raw(man['repo'], man['ref'], man['path'], man['sha256'], path)
    print(f"{state:10s} registry snapshot  {man['sha256'][:12]}")


def verify_template() -> Path:
    """Verify every shared module on each use, not just when initially fetched."""
    man = json.loads((ROOT / 'data/template.json').read_text())
    base = CACHE / 'template' / 'src' / 'gems57'
    for item in man['files']:
        name = Path(item['path'])
        if name.name != item['path'] or name.suffix != '.py':
            raise ValueError('invalid template module name')
        file = base / name
        if not file.is_file() or sha256(file) != item['sha256']:
            raise ValueError(f'shared template missing or hash-mismatched: {name}; run scripts/fetch_inputs.py --template-only')
    return base.parent
