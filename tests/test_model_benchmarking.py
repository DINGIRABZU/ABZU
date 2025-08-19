import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.helpers.config_stub import build_settings

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)

sp_pkg = types.ModuleType("SPIRAL_OS")
sp_pkg.qnl_engine = types.SimpleNamespace(
    parse_input=lambda text: {"tone": "neutral"},
    hex_to_song=lambda hex_input, duration_per_byte=0.05: ([], []),
)
sp_pkg.symbolic_parser = types.SimpleNamespace(
    parse_intent=lambda d: [],
    _gather_text=lambda d: "",
    _INTENTS={},
)
sys.modules.setdefault("SPIRAL_OS", sp_pkg)
sys.modules["SPIRAL_OS.qnl_engine"] = sp_pkg.qnl_engine
sys.modules["SPIRAL_OS.symbolic_parser"] = sp_pkg.symbolic_parser
sys.modules.setdefault("training_guide", types.SimpleNamespace(log_result=lambda *a, **k: None))

from rag.orchestrator import MoGEOrchestrator
from INANNA_AI import db_storage
from INANNA_AI import gate_orchestrator
from INANNA_AI import response_manager
import rag.orchestrator as orch_mod
import core.model_selector as ms_mod

orch_mod.vector_memory.add_vector = lambda *a, **k: None
orch_mod.vector_memory.query_vectors = lambda *a, **k: []
ms_mod.vector_memory = orch_mod.vector_memory


def test_orchestrator_logs_and_updates(tmp_path, monkeypatch):
    db = tmp_path / "bench.db"
    db_storage.init_db(db)

    monkeypatch.setattr(db_storage, "DB_PATH", db)

    orch = MoGEOrchestrator(db_path=db)
    monkeypatch.setattr(response_manager.corpus_memory, "search_corpus", lambda *a, **k: [("p", "s")])
    monkeypatch.setattr(orch._responder, "generate_reply", lambda t, info: "reply text")

    weight_before = orch._model_selector.model_weights["glm"]
    orch.route("hello", {"emotion": "neutral"})
    weight_after = orch._model_selector.model_weights["glm"]
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
