import json
from agents.razar import quarantine_manager as qm


def test_quarantine_metadata(tmp_path, monkeypatch):
    quarantine_dir = tmp_path / "quarantine"
    log_file = tmp_path / "log.md"
    monkeypatch.setattr(qm, "QUARANTINE_DIR", quarantine_dir)
    monkeypatch.setattr(qm, "LOG_FILE", log_file)

    component = {"name": "alpha"}
    qm.quarantine_component(component, "boom")
    data = json.loads((quarantine_dir / "alpha.json").read_text(encoding="utf-8"))
    assert data["reason"] == "boom"
    assert data["attempts"] == 1
    assert data["patches_applied"] == []

    qm.record_patch("alpha", "fix1")
    data = json.loads((quarantine_dir / "alpha.json").read_text(encoding="utf-8"))
    assert data["patches_applied"] == ["fix1"]
