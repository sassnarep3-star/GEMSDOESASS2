"""Pinned audit fetches must not damage an existing cache on failure."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import audit_snapshot


def test_audit_fetch_stages_uniquely_and_hashes_before_replace(tmp_path, monkeypatch):
    target = tmp_path / "asset.tif"
    target.write_bytes(b"previous")
    old_partial = tmp_path / "asset.tif.partial"
    old_partial.write_bytes(b"unrelated user bytes")
    expected = b"verified"
    import hashlib
    spec = {"sha256": hashlib.sha256(expected).hexdigest(), "site": "test",
            "path": "data/asset.tif", "ref": "immutable"}
    def download(payload):
        def run(*args, stdout, **kwargs):
            stdout.write(payload)
            return SimpleNamespace(returncode=0, stderr=b"")
        return run
    monkeypatch.setattr(audit_snapshot.subprocess, "run", download(b"corrupt"))
    with pytest.raises(ValueError, match="Hash mismatch"):
        audit_snapshot.fetch_pinned(spec, target, True)
    assert target.read_bytes() == b"previous"
    assert old_partial.read_bytes() == b"unrelated user bytes"
    monkeypatch.setattr(audit_snapshot.subprocess, "run", download(expected))
    assert audit_snapshot.fetch_pinned(spec, target, True) == target
    assert target.read_bytes() == expected
    assert old_partial.read_bytes() == b"unrelated user bytes"
    assert set(tmp_path.iterdir()) == {target, old_partial}
