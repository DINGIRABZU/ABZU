from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_usage_dashboard_metrics(monkeypatch):
    calls = {}
    fake_st = types.SimpleNamespace(
        set_page_config=lambda **kw: None,
        title=lambda *a, **k: None,
        metric=lambda label, value: calls.setdefault(label, value),
        subheader=lambda *a, **k: None,
        dataframe=lambda *a, **k: None,
    )
    class FakeDF(list):
        def tail(self, n):
            return self

    fake_pd = types.SimpleNamespace(DataFrame=lambda data: FakeDF(data))
    fake_cml = types.SimpleNamespace(load_interactions=lambda: [1, 2, 3])
    fake_fb = types.SimpleNamespace(load_feedback=lambda: [1])
    fake_core = types.ModuleType("core")
    fake_core.feedback_logging = fake_fb
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setitem(sys.modules, "pandas", fake_pd)
    monkeypatch.setitem(sys.modules, "corpus_memory_logging", fake_cml)
    monkeypatch.setitem(sys.modules, "core", fake_core)

    usage = importlib.import_module("dashboard.usage")
    importlib.reload(usage)

    assert calls["Total interactions"] == 3
    assert calls["Feedback entries"] == 1
