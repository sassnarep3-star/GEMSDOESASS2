"""The shared cache wrapper must not overwrite incomplete or conflicting inputs."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import prepare_data


def test_feature_assembly_refuses_existing_partial(tmp_path, monkeypatch):
    values = {name: name.encode() for name in ("sample_submission.tif", "labels.tif", "existing_faults.tif")}
    bridge = tmp_path / "data/bridge"
    bridge.mkdir(parents=True)
    for name, content in values.items():
        (bridge / name).write_bytes(content)
    pin = {f"data/official/{name}": prepare_data.digest(bridge / name) for name in values}
    pin["data/official/training_features.tif"] = "f" * 64
    template = SimpleNamespace(PIN=pin, PARTS=[], assemble_features=lambda _: pytest.fail("must not assemble"))
    monkeypatch.setattr(prepare_data, "load_shared_template", lambda _: template)
    partial = tmp_path / ".cache/training_features.tif.partial"
    partial.parent.mkdir()
    partial.write_bytes(b"preserve")
    with pytest.raises(ValueError, match="partial assembly"):
        prepare_data.prepare(tmp_path, fetch=True, cache_bands=False)
    assert partial.read_bytes() == b"preserve"
    assert not (tmp_path / "data/official/training_features.tif").exists()
