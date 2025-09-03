import json

from razar import boot_orchestrator


def test_events_list_populated(tmp_path, monkeypatch):
    state_file = tmp_path / "razar_state.json"
    monkeypatch.setattr(boot_orchestrator, "STATE_FILE", state_file)
    monkeypatch.setattr(boot_orchestrator, "LOGS_DIR", tmp_path)

    class DummyProc:
        returncode = 0

        def wait(self):  # pragma: no cover - behaviour is trivial
            return 0

    monkeypatch.setattr(
        boot_orchestrator.subprocess, "Popen", lambda *a, **k: DummyProc()
    )
    monkeypatch.setattr(
        boot_orchestrator.mission_logger, "log_event", lambda *a, **k: None
    )

    boot_orchestrator._ensure_glm4v([])
    data = json.loads(state_file.read_text())
    assert data["events"], "events list should not be empty"
    assert data["events"][0]["event"] == "model_launch"
