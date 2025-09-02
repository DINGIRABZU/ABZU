"""Tests for checkpoint manager."""

from pathlib import Path
import json

from agents.razar import checkpoint_manager as cm


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    assert cm.load_checkpoint(path) == ""
    cm.save_checkpoint("alpha", path)
    cm.save_checkpoint("beta", path)
    assert cm.load_checkpoint(path) == "beta"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["history"] == ["alpha", "beta"]
    cm.clear_checkpoint(path)
    assert cm.load_checkpoint(path) == ""
