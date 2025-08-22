import importlib.util
import sys
import types
from pathlib import Path

from streamlit_stub import StreamlitStub


def _run_dashboard(monkeypatch, file_name: str, extra_modules: dict[str, types.ModuleType]) -> StreamlitStub:
    st = StreamlitStub()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    for name, module in extra_modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    dummy_pd = types.ModuleType("pandas")
    class DummyDF:
        def __init__(self, data):
            self.data = data
        def tail(self, n):
            return self
    dummy_pd.DataFrame = DummyDF
    monkeypatch.setitem(sys.modules, "pandas", dummy_pd)
    path = Path(__file__).resolve().parents[1] / "dashboard" / file_name
    spec = importlib.util.spec_from_file_location(file_name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return st


def test_usage_dashboard(monkeypatch):
    fake_corpus = types.ModuleType("corpus_memory_logging")
    fake_corpus.load_interactions = lambda: [{"a": 1}, {"a": 2}]
    fake_feedback = types.ModuleType("feedback_logging")
    fake_feedback.load_feedback = lambda: [{"b": 1}]

    st = _run_dashboard(
        monkeypatch,
        "usage.py",
        {
            "corpus_memory_logging": fake_corpus,
            "feedback_logging": fake_feedback,
        },
    )

    assert ("title", "Usage Metrics") in st.calls
    assert ("metric", "Total interactions", 2) in st.calls
    assert ("metric", "Feedback entries", 1) in st.calls
    assert sum(1 for c in st.calls if c[0] == "dataframe") == 2


def test_usage_dashboard_no_data(monkeypatch):
    fake_corpus = types.ModuleType("corpus_memory_logging")
    fake_corpus.load_interactions = lambda: []
    fake_feedback = types.ModuleType("feedback_logging")
    fake_feedback.load_feedback = lambda: []

    st = _run_dashboard(
        monkeypatch,
        "usage.py",
        {
            "corpus_memory_logging": fake_corpus,
            "feedback_logging": fake_feedback,
        },
    )

    assert ("metric", "Total interactions", 0) in st.calls
    assert ("metric", "Feedback entries", 0) in st.calls
    assert not any(c[0] == "dataframe" for c in st.calls)