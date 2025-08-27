from pathlib import Path
from agents.razar import checkpoint_manager as cm


def test_checkpoint_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    assert cm.load_checkpoint(path) == ""
    cm.save_checkpoint("alpha", path)
    assert cm.load_checkpoint(path) == "alpha"
    cm.clear_checkpoint(path)
    assert cm.load_checkpoint(path) == ""
