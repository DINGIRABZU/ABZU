import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from orchestrator import MoGEOrchestrator
from INANNA_AI import db_storage
from INANNA_AI import gate_orchestrator
from INANNA_AI import response_manager


def test_orchestrator_logs_and_updates(tmp_path, monkeypatch):
    db = tmp_path / "bench.db"
    db_storage.init_db(db)

    monkeypatch.setattr(db_storage, "DB_PATH", db)

    orch = MoGEOrchestrator(db_path=db)
    monkeypatch.setattr(response_manager.corpus_memory, "search_corpus", lambda *a, **k: [("p", "s")])
    monkeypatch.setattr(orch._responder, "generate_reply", lambda t, info: "reply text")

    weight_before = orch._model_weights["glm"]
    orch.route("hello", {"emotion": "neutral"})
    weight_after = orch._model_weights["glm"]
    metrics = db_storage.fetch_benchmarks(db_path=db)

    assert len(metrics) == 1
    assert metrics[0]["model"] == "glm"
    assert weight_after != weight_before


def test_gate_orchestrator_benchmark(tmp_path):
    db = tmp_path / "bench.db"
    db_storage.init_db(db)

    gate = gate_orchestrator.GateOrchestrator(db_path=db)
    res = gate.benchmark("hello")
    metrics = db_storage.fetch_benchmarks(db_path=db)

    assert res["out_text"]
    assert metrics and metrics[0]["model"] == "gate"
