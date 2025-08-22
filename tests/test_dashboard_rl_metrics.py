import importlib.util
import sys
import types
from pathlib import Path

from streamlit_stub import StreamlitStub
import INANNA_AI


def _run_dashboard(monkeypatch, fetch_feedback, threshold):
    st = StreamlitStub()
    monkeypatch.setitem(sys.modules, "streamlit", st)

    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_feedback = fetch_feedback
    fake_adaptive = types.ModuleType("adaptive_learning")

    class DummyThresh:
        def __init__(self, value):
            self.threshold = value

    fake_adaptive.THRESHOLD_AGENT = DummyThresh(threshold)
    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.adaptive_learning", fake_adaptive)
    monkeypatch.setattr(INANNA_AI, "db_storage", fake_db, raising=False)
    monkeypatch.setattr(INANNA_AI, "adaptive_learning", fake_adaptive, raising=False)
    dummy_pd = types.ModuleType("pandas")
    class DummyDF:
        def __init__(self, data):
            self.data = data
        def set_index(self, *args, **kwargs):
            return self
        def __getitem__(self, key):
            return self
        def tail(self, n=20):
            return self
    dummy_pd.DataFrame = DummyDF
    monkeypatch.setitem(sys.modules, "pandas", dummy_pd)

    path = Path(__file__).resolve().parents[1] / "dashboard" / "rl_metrics.py"
    spec = importlib.util.spec_from_file_location("rl_metrics", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return st


def test_rl_metrics_renders(monkeypatch):
    def fb(limit=100):
        return [
            {
                "timestamp": "0",
                "satisfaction": 1,
                "ethical_alignment": 1,
                "existential_clarity": 1,
            }
        ]

    st = _run_dashboard(monkeypatch, fb, 0.42)
    assert any(c[0] == "line_chart" for c in st.calls)
    assert ("markdown", "**Current threshold:** 0.42") in st.calls


def test_rl_metrics_no_feedback(monkeypatch):
    st = _run_dashboard(monkeypatch, lambda **_: [], 0.5)
    assert ("write", "No feedback data available.") in st.calls
