import importlib.util
import sys
import types
from pathlib import Path

from streamlit_stub import StreamlitStub

import INANNA_AI

def test_dashboard_app_no_data(monkeypatch):
    st = StreamlitStub()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: []

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go = types.ModuleType("gate_orchestrator")
    fake_go.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go)
    monkeypatch.setattr(INANNA_AI, "db_storage", fake_db, raising=False)
    monkeypatch.setattr(INANNA_AI, "gate_orchestrator", fake_go, raising=False)

    path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    spec = importlib.util.spec_from_file_location("app", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert ("write", "No benchmark data available.") in st.calls
    assert ("markdown", "**Predicted best model:** `mock-model`") in st.calls
