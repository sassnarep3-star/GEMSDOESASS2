"""Fail-closed decision, provenance, restoration and upstream-probe regressions."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import check_upstream, fetch_data, prepare_data
from scripts.build_run_card import build_card

ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_every_vendored_shared_file_matches_its_pinned_bytes():
    manifest = json.loads((ROOT / "vendor/PROVENANCE.json").read_text())
    for name, expected in manifest["files"].items():
        assert prepare_data.digest(ROOT / name) == expected, name
    assert manifest["files"]["vendor/gems57/evaluate_holdout.py"] == "ad86640b46f3c5fc6b1aceec4c4bfc82d03e35008b37ab2a8ad6076e6810ff3a"


@pytest.mark.parametrize("name", [
    "evaluate_holdout.py", "submission_writer.py", "run_hvfd_experiments.py",
    "run_sass2_xghf.py", "generate_figures_and_site_data.py", "audit_nine_focus_sites.py",
    "prepare_hvfd_data.py", "generate_submission.py", "build_submission.py",
    "run_pipeline.py", "experiments.py", "check_uniqueness.py", "check_uniqueness_sgmc.py",
    "finalize_card.py", "build_site.py", "sgmc_calibration.py",
])
def test_legacy_execution_and_import_fail_before_writing(name):
    script = ROOT / "scripts" / name
    run = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert run.returncode == 2 and "DO NOT SUBMIT" in run.stderr
    code = "import runpy; runpy.run_path(%r, run_name='import_probe')" % str(script)
    imported = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=10)
    assert imported.returncode != 0 and "RuntimeError" in imported.stderr


def test_negative_card_rebuild_is_deterministic_and_refuses_changed_evidence():
    audit = json.loads((ROOT / "docs/data/audit.json").read_text())
    upstream = json.loads((ROOT / "docs/data/upstream-check.json").read_text())
    restoration = json.loads((ROOT / "evidence/data_restoration_20261028.json").read_text())
    result = build_card(audit, upstream, restoration)
    assert result == json.loads((ROOT / "docs/data/run-card.json").read_text())
    assert result == json.loads((ROOT / "docs/data/latest-run-card.json").read_text())
    assert result["verdict"] == "negative" and not result["ok_to_submit"]
    assert result["raster_sha256"] is None and result["holdout_dti"]["ci95"] is None
    with pytest.raises(ValueError, match="Upstream"):
        build_card(audit, {**upstream, "ready_for_shared_holdout": True}, restoration)
    changed = {**audit, "new_tiff_created": True}
    with pytest.raises(ValueError, match="scope changed"):
        build_card(changed, upstream, restoration)


def test_ledger_never_relabels_user_reports_as_receipt_confirmed():
    with (ROOT / "docs/data/score-ledger.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert not any("ORGANIZER-CONFIRMED" in str(row) for row in rows)
    owner = [row for row in rows if row["evidence_class"] in ("user-report", "owner-report")]
    assert len(owner) > 100
    assert all("USER-REPORTED / UNVERIFIED" in row["status"] for row in owner)
    local = [row for row in rows if row["evidence_class"] == "historical-unverified"]
    assert local and all("DO NOT SUBMIT" in row["status"] for row in local)
    public = [row for row in rows if row["evidence_class"] == "official-public-snapshot"]
    assert len(public) == 1 and public[0]["score"] == "0.4544"
    assert "not a score receipt" in public[0]["status"]


def entry_for(data: bytes, *, parts: list[str] | None = None) -> dict:
    entry = {"id": "test", "repo": "owner/repo", "ref": "immutable", "dest": "asset.tif",
             "group": "test", "sha256": sha(data), "bytes": len(data)}
    entry["parts" if parts is not None else "path"] = parts if parts is not None else "source.tif"
    return entry


def test_atomic_single_fetch_preserves_existing_bytes_on_error(tmp_path, monkeypatch):
    target = tmp_path / "asset.tif"
    target.write_bytes(b"existing user data")
    entry = entry_for(b"expected")
    monkeypatch.setattr(fetch_data, "_download", lambda repo, ref, path, dest: dest.write_bytes(b"bad"))
    with pytest.raises(ValueError, match="destination not replaced"):
        fetch_data.fetch_entry(entry, target)
    assert target.read_bytes() == b"existing user data"
    assert list(tmp_path.iterdir()) == [target]
    def failed(*args):
        raise subprocess.CalledProcessError(1, "gh")
    monkeypatch.setattr(fetch_data, "_download", failed)
    with pytest.raises(subprocess.CalledProcessError):
        fetch_data.fetch_entry(entry, target)
    assert target.read_bytes() == b"existing user data" and list(tmp_path.iterdir()) == [target]
    monkeypatch.setattr(fetch_data, "_download", lambda repo, ref, path, dest: dest.write_bytes(b"expected"))
    assert not fetch_data.fetch_entry(entry, target)["cached"]
    assert target.read_bytes() == b"expected"
    monkeypatch.setattr(fetch_data, "_download", failed)
    assert fetch_data.fetch_entry(entry, target)["cached"]


def test_multipart_assembly_verifies_before_replace(tmp_path, monkeypatch):
    target = tmp_path / "asset.tif"
    target.write_bytes(b"keep this")
    entry = entry_for(b"onetwo", parts=["1", "2"])
    pieces = {"1": b"one", "2": b"BROKEN"}
    monkeypatch.setattr(fetch_data, "_download", lambda repo, ref, part, dest: dest.write_bytes(pieces[part]))
    with pytest.raises(ValueError):
        fetch_data.fetch_entry(entry, target)
    assert target.read_bytes() == b"keep this"
    pieces["2"] = b"two"
    assert fetch_data.fetch_entry(entry, target)["sha256"] == sha(b"onetwo")
    assert target.read_bytes() == b"onetwo" and list(tmp_path.iterdir()) == [target]


def test_fetch_refuses_even_a_valid_symlink(tmp_path):
    real = tmp_path / "real"
    real.write_bytes(b"expected")
    link = tmp_path / "asset.tif"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="non-regular"):
        fetch_data.fetch_entry(entry_for(b"expected"), link)
    assert link.is_symlink() and real.read_bytes() == b"expected"


def test_reference_link_preserves_wrong_file_and_broken_symlink(tmp_path):
    bridge = tmp_path / "data/bridge/sample_submission.tif"
    bridge.parent.mkdir(parents=True)
    bridge.write_bytes(b"verified")
    target = tmp_path / "data/official/sample_submission.tif"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"user data")
    with pytest.raises(ValueError, match="not overwriting"):
        prepare_data.verify_or_link(tmp_path, target.name, sha(b"verified"))
    assert target.read_bytes() == b"user data"
    target.unlink()
    target.symlink_to(tmp_path / "absent")
    with pytest.raises(ValueError, match="Broken"):
        prepare_data.verify_or_link(tmp_path, target.name, sha(b"verified"))
    assert target.is_symlink()


def fake_builder(root: Path, source_sha: str) -> dict:
    cache = root / ".cache/features"
    cache.mkdir(parents=True)
    bands = []
    for number in range(1, 20):
        file = cache / f"band-{number:02d}.npy"
        file.write_bytes(f"band-{number}".encode())
        bands.append({"band": number, "cache_file": str(file.relative_to(root)), "sha256": prepare_data.digest(file)})
    report = {"count": 19, "source_sha256": source_sha, "bands": bands}
    (root / "evidence").mkdir()
    (root / "evidence/feature_cache.json").write_text(json.dumps(report))
    return report


def test_band_cache_staged_reused_and_conflicts_fail_closed(tmp_path):
    source = "f" * 64
    (tmp_path / "data/official").mkdir(parents=True)
    builder = SimpleNamespace(cache_bands=lambda stage: fake_builder(stage, source))
    report, created = prepare_data.ensure_band_cache(tmp_path, builder, source)
    assert created and report["count"] == 19
    assert prepare_data.ensure_band_cache(tmp_path, builder, source)[1] is False
    band = tmp_path / ".cache/features/band-02.npy"
    band.write_bytes(b"user modified cache")
    with pytest.raises(ValueError, match="not overwriting"):
        prepare_data.ensure_band_cache(tmp_path, builder, source)
    assert band.read_bytes() == b"user modified cache"


def test_staged_cache_does_not_overwrite_an_existing_receipt(tmp_path):
    source = "f" * 64
    (tmp_path / "data/official").mkdir(parents=True)
    receipt = tmp_path / "evidence/feature_cache.json"
    receipt.parent.mkdir()
    receipt.write_text('{"user": "preserve"}')
    builder = SimpleNamespace(cache_bands=lambda stage: fake_builder(stage, source))
    with pytest.raises(ValueError, match="not overwriting"):
        prepare_data.ensure_band_cache(tmp_path, builder, source)
    assert json.loads(receipt.read_text()) == {"user": "preserve"}
    assert not (tmp_path / ".cache/features").exists()


def write_probe_module(root: Path, correct: bool):
    package = root / "src/gems32"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "release_gate.py").write_text(
        "def compare_registry(*args, **kwargs):\n"
        "    return {'comparisons':[{'within_3px_fraction': 1.0, 'spearman': 0.0}], 'passed': %r}\n" % (not correct)
    )
    (package / "holdout.py").write_text(
        "import numpy as np\n"
        "class PreparedCell:\n"
        "    def __init__(self, **kw): self.__dict__.update(kw)\n"
        "def evaluate_hide_and_recover(*args, **kwargs):\n"
        "    return {'folds': {'empty': {'fp': 1.0}}, '_block_totals': [np.zeros(1), np.array([%s])]}\n" % (1.0 if correct else 0.0)
    )


@pytest.mark.parametrize("correct, expected_code", [(False, 2), (True, 0)])
def test_synthetic_shared_probes_detect_both_defects(tmp_path, correct, expected_code):
    write_probe_module(tmp_path, correct)
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_upstream.py"), "--template-root", str(tmp_path)],
                            cwd=ROOT, capture_output=True, text=True, timeout=15)
    assert result.returncode == expected_code, result.stderr
    report = json.loads(result.stdout)
    assert report["surface_duplicate"]["correct"] is correct
    assert report["zero_truth_false_positive_accounting"]["correct"] is correct
    assert report["ready_for_shared_holdout"] is correct
    assert report["checked_utc"].endswith("Z")


def test_probe_wont_hash_new_files_while_executing_cached_modules(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "gems32", SimpleNamespace())
    with pytest.raises(RuntimeError, match="already imported"):
        check_upstream.probe(tmp_path)
