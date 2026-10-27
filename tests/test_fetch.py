import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from gems_audit.fetch import fetch_raw, sha256


def test_fetch_verified_atomically_and_uses_cache(tmp_path, monkeypatch):
    payload = b'source bytes'
    calls = []
    def fake_run(command, *, stdout, check):
        calls.append(command)
        stdout.write(payload)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr('gems_audit.fetch.subprocess.run', fake_run)
    target = tmp_path / 'out.tif'
    digest = hashlib.sha256(payload).hexdigest()
    assert fetch_raw('a/b', 'abcdef', 'file.tif', digest, target) == 'downloaded'
    assert sha256(target) == digest
    assert fetch_raw('a/b', 'abcdef', 'file.tif', digest, target) == 'cached'
    assert len(calls) == 1


def test_hash_mismatch_never_replaces_existing_data(tmp_path, monkeypatch):
    target = tmp_path / 'out.tif'
    target.write_bytes(b'old')
    def fake_run(command, *, stdout, check):
        stdout.write(b'bad')
    monkeypatch.setattr('gems_audit.fetch.subprocess.run', fake_run)
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        fetch_raw('a/b', 'ref', 'file', 'f' * 64, target)
    assert target.read_bytes() == b'old'
    assert not list(tmp_path.glob('.fetch-*'))


def test_shared_template_is_hash_checked_each_time(tmp_path, monkeypatch):
    import json
    import gems_audit.fetch as fetch
    monkeypatch.setattr(fetch, 'ROOT', tmp_path)
    monkeypatch.setattr(fetch, 'CACHE', tmp_path / '.cache')
    (tmp_path / 'data').mkdir()
    base = tmp_path / '.cache/template/src/gems57'
    base.mkdir(parents=True)
    source = base / 'gates.py'
    source.write_text('unchanged')
    expected = hashlib.sha256(b'unchanged').hexdigest()
    (tmp_path / 'data/template.json').write_text(json.dumps({'files': [{'path': 'gates.py', 'sha256': expected}]}))
    assert fetch.verify_template() == base.parent
    source.write_text('modified')
    with pytest.raises(ValueError, match='hash-mismatched'):
        fetch.verify_template()
