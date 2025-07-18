import importlib
from pathlib import Path

from INANNA_AI import db_storage, gate_orchestrator


def test_predictive_model(tmp_path):
    db = tmp_path / "bench.db"
    db_storage.init_db(db)
    models = ["glm", "deepseek", "mistral"]
    for m in models:
        db_storage.save_interaction("hello", "neutral", "resp", db_path=db)
        db_storage.log_benchmark(m, 0.1, 0.9, 0.9, db_path=db)
    gate = gate_orchestrator.GateOrchestrator(db_path=db)
    pred = gate.predict_best_llm()
    assert pred in models


def test_dashboard_import():
    mod = importlib.import_module("dashboard.app")
    assert mod is not None

