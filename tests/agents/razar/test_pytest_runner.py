"""Tests for pytest runner."""

import json


from agents.razar import pytest_runner as pr


def test_run_pytest_logs_and_plans(monkeypatch, tmp_path):
    log_path = tmp_path / "logs" / "pytest_priority.log"
    map_path = tmp_path / "tests" / "priority_map.yaml"
    state_path = tmp_path / "logs" / "pytest_state.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    map_path.write_text("P1:\n  - tests/test_example.py\n", encoding="utf-8")

    module_path = tmp_path / "example.py"
    module_path.write_text("""def ok():\n    return True\n""", encoding="utf-8")

    def fake_main(args):
        return 1

    monkeypatch.setattr(pr.pytest, "main", fake_main)
    monkeypatch.setattr(
        pr, "_last_failed", lambda root: "tests/test_example.py::test_fail"
    )
    monkeypatch.setattr(pr, "_attempt_repair", lambda *a, **k: False)
    monkeypatch.setattr(
        pr,
        "_guess_module_path",
        lambda root, node: (module_path, root / node.split("::")[0]),
    )

    called = {}

    def fake_log_event(event, component, status, details=None):
        called["log"] = (event, component, status, details)

    def fake_plan():
        called["plan"] = True
        return {module_path.stem: {"steps": ["x"]}}

    def fake_crown(*args, **kwargs):
        called["crown"] = True
        return ""

    monkeypatch.setattr(pr.mission_logger, "log_event", fake_log_event)
    monkeypatch.setattr(pr.planning_engine, "plan", fake_plan)
    monkeypatch.setattr(pr, "_send_failure_to_crown", fake_crown)

    code = pr.run_pytest(["P1"], False, log_path, map_path, state_path)
    assert code != 0
    assert state_path.exists()
    state = json.loads(state_path.read_text())
    assert state["tier"] == "P1"
    assert "tests/test_example.py" in state["nodeid"]
    assert called["plan"] is True
    assert called["log"][1] == module_path.stem
    assert called["crown"] is True
