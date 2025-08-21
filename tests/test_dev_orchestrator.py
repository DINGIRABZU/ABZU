import pytest

from tools import dev_orchestrator


@pytest.fixture()
def mock_glm_complete(monkeypatch):
    """Stub out GLMIntegration.complete to avoid external calls."""

    def _fake_complete(self, prompt: str) -> str:
        return "stub"

    monkeypatch.setattr(
        dev_orchestrator.GLMIntegration,
        "complete",
        _fake_complete,
    )
    return _fake_complete


@pytest.fixture()
def stub_vector_memory(monkeypatch):
    """Stub vector_memory search and add_vector to be no-ops."""
    monkeypatch.setattr(
        dev_orchestrator.vector_memory,
        "search",
        lambda *_, **__: [],
    )
    monkeypatch.setattr(
        dev_orchestrator.vector_memory,
        "add_vector",
        lambda *_, **__: None,
    )


def test_run_dev_cycle_dispatches_tasks(
    monkeypatch, mock_glm_complete, stub_vector_memory
):
    calls = {"code": [], "review": []}

    class MockPlanner:
        def __init__(self, name, role, glm, objective, queue):
            self.queue = queue

        def plan(self):
            self.queue.put("task 1")
            return ["task 1"]

    class MockCoder:
        def __init__(self, name, role, glm, objective, queue):
            pass

        def code(self, task):
            calls["code"].append(task)
            return f"code for {task}"

    class MockReviewer:
        def __init__(self, name, role, glm, objective, queue):
            pass

        def review(self, task, code):
            calls["review"].append((task, code))
            return f"review for {task}"

    monkeypatch.setattr(dev_orchestrator, "Planner", MockPlanner)
    monkeypatch.setattr(dev_orchestrator, "Coder", MockCoder)
    monkeypatch.setattr(dev_orchestrator, "Reviewer", MockReviewer)

    result = dev_orchestrator.run_dev_cycle("test objective")

    assert calls["code"] == ["task 1"]
    assert calls["review"] == [("task 1", "code for task 1")]
    assert result["plan"] == ["task 1"]
    assert result["results"] == [
        {
            "task": "task 1",
            "code": "code for task 1",
            "review": "review for task 1",
        }
    ]


def test_run_tests_skips_when_pytest_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(
        dev_orchestrator.shutil,
        "which",
        lambda _: None,
    )
    monkeypatch.setattr(
        dev_orchestrator,
        "log_interaction",
        lambda *_, **__: None,
    )
    result = dev_orchestrator._run_tests(tmp_path)
    assert result["returncode"] is None
    assert "pytest not found" in result["output"]
