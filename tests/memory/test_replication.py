"""Tests for distributed memory replication."""

import json
from distributed_memory import DistributedMemory


def _make_config(tmp_path):
    cfg = tmp_path / "memory_backends.toml"
    cfg.write_text(
        f"""
[primary]
type = "json"
path = "{tmp_path / 'primary.json'}"

[fallback]
type = "json"
path = "{tmp_path / 'fallback.json'}"
"""
    )
    return cfg


def test_primary_outage_uses_fallback(tmp_path, monkeypatch):
    cfg = _make_config(tmp_path)
    dm = DistributedMemory.from_config(cfg)
    dm.backup("a", [1.0, 2.0], {"n": "a"})

    # Ensure replication wrote to both files
    p_data = json.loads((tmp_path / "primary.json").read_text())
    f_data = json.loads((tmp_path / "fallback.json").read_text())
    assert p_data == f_data

    # Simulate primary outage
    def boom():
        raise RuntimeError("down")

    monkeypatch.setattr(dm.primary, "restore", boom)

    restored = dm.restore()
    assert "a" in restored
    assert restored["a"][0] == [1.0, 2.0]


def test_fallback_outage_ignored(tmp_path, monkeypatch):
    cfg = _make_config(tmp_path)
    dm = DistributedMemory.from_config(cfg)
    dm.backup("a", [1.0, 2.0], {"n": "a"})

    def boom():
        raise RuntimeError("down")

    monkeypatch.setattr(dm.fallback, "restore", boom)

    restored = dm.restore()
    assert "a" in restored
    assert restored["a"][0] == [1.0, 2.0]
