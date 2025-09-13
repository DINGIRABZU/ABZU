"""Tests for dashboard app."""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import UnknownElement


def test_dashboard_app_renders_metrics(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: {
        "timestamp": pd.Series(["2024-01-01T00:00:00"]),
        "response_time": pd.Series([0.1]),
        "coherence": pd.Series([0.9]),
        "relevance": pd.Series([0.95]),
    }

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run(timeout=10)

    assert any(isinstance(el, UnknownElement) for el in at.main)
    assert any(m.value == "**Predicted best model:** `mock-model`" for m in at.markdown)


def test_dashboard_app_handles_no_metrics(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: []

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run(timeout=10)

    assert any(m.value == "No benchmark data available." for m in at.markdown)
    assert any(m.value == "**Predicted best model:** `mock-model`" for m in at.markdown)


def test_dashboard_app_multiple_metrics(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: {
        "timestamp": pd.Series(["2024-01-01T00:00:00", "2024-01-02T00:00:00"]),
        "response_time": pd.Series([0.1, 0.2]),
        "coherence": pd.Series([0.9, 0.85]),
        "relevance": pd.Series([0.95, 0.9]),
    }

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run(timeout=10)

    assert any(m.value == "**Predicted best model:** `mock-model`" for m in at.markdown)


def test_dashboard_app_fetch_failure(monkeypatch, caplog):
    def broken_fetch():
        raise RuntimeError("db down")

    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = broken_fetch

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    with caplog.at_level(logging.ERROR):
        at = AppTest.from_file(app_path)
        at.run(timeout=10)

    assert "Failed to fetch benchmarks" in caplog.text
    assert any(m.value == "No benchmark data available." for m in at.markdown)
    assert any(m.value == "**Predicted best model:** `mock-model`" for m in at.markdown)


def test_dashboard_app_prediction_failure(monkeypatch, caplog):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: []

    class DummyGO:
        def predict_best_llm(self):
            raise RuntimeError("boom")

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    with caplog.at_level(logging.ERROR):
        at = AppTest.from_file(app_path)
        at.run(timeout=10)

    assert "Failed to predict best model" in caplog.text
    assert any(m.value == "No benchmark data available." for m in at.markdown)
    assert any(m.value == "**Predicted best model:** `unknown`" for m in at.markdown)


def test_dashboard_app_prediction_none(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: []

    class DummyGO:
        def predict_best_llm(self):
            return None

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run(timeout=10)

    assert any(m.value == "No benchmark data available." for m in at.markdown)
    assert any(m.value == "**Predicted best model:** `None`" for m in at.markdown)


def test_dashboard_app_large_metrics(monkeypatch):
    fake_db = types.ModuleType("db_storage")
    fake_db.fetch_benchmarks = lambda: {
        "timestamp": pd.Series([f"2024-01-{i:02d}T00:00:00" for i in range(1, 101)]),
        "response_time": pd.Series([i * 0.1 for i in range(1, 101)]),
        "coherence": pd.Series(np.full(100, 0.8)),
        "relevance": pd.Series([0.85] * 100),
    }

    class DummyGO:
        def predict_best_llm(self):
            return "mock-model"

    fake_go_mod = types.ModuleType("gate_orchestrator")
    fake_go_mod.GateOrchestrator = DummyGO

    monkeypatch.setitem(sys.modules, "INANNA_AI.db_storage", fake_db)
    monkeypatch.setitem(sys.modules, "INANNA_AI.gate_orchestrator", fake_go_mod)

    app_path = Path(__file__).resolve().parents[1] / "src" / "dashboard" / "app.py"
    at = AppTest.from_file(app_path)
    at.run(timeout=10)

    assert any(isinstance(el, UnknownElement) for el in at.main)
    assert any(m.value == "**Predicted best model:** `mock-model`" for m in at.markdown)
