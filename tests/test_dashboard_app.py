import sys
import types
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import UnknownElement

pytestmark = pytest.mark.skip(reason="requires benchmarks table")


def test_dashboard_app_renders_metrics(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: [
        {
            "timestamp": "2024-01-01T00:00:00",
            "response_time": 0.1,
            "coherence": 0.9,
            "relevance": 0.95,
        }
    ]

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run()

    assert at.title[0].value == "LLM Performance Metrics"
    assert isinstance(at.main[1], UnknownElement)
    assert at.markdown[0].value == "**Predicted best model:** `mock-model`"
