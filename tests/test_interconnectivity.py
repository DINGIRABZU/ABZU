import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)

import orchestrator
from orchestrator import MoGEOrchestrator
from core import context_tracker, language_engine


class DummyConnector:
    def __init__(self):
        self.calls = []

    def start_call(self, path: str) -> None:
        self.calls.append(path)


def test_avatar_and_call_sequence(monkeypatch):
    connector = DummyConnector()
    language_engine.register_connector(connector)

    monkeypatch.setattr(
        language_engine.tts_coqui,
        "synthesize_speech",
        lambda text, emo: f"/tmp/{emo}.wav",
    )
    monkeypatch.setattr(
        "INANNA_AI.corpus_memory.search_corpus",
        lambda *a, **k: [("p", "snippet")],
    )
    monkeypatch.setattr(orchestrator, "log_interaction", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator, "load_interactions", lambda: [])
    monkeypatch.setattr(orchestrator, "update_insights", lambda logs: None)
    monkeypatch.setattr(orchestrator, "load_insights", lambda: {})
    monkeypatch.setattr(orchestrator.learning_mutator, "propose_mutations", lambda d: [])
    monkeypatch.setattr(orchestrator.qnl_engine, "parse_input", lambda t: {"tone": "neutral"})
    monkeypatch.setattr(orchestrator.symbolic_parser, "parse_intent", lambda d: [])
    monkeypatch.setattr(orchestrator.reflection_loop, "run_reflection_loop", lambda *a, **k: None)

    orch = MoGEOrchestrator()

    orch.handle_input("appear to me")
    assert context_tracker.state.avatar_loaded is True
    assert context_tracker.state.in_call is False

    orch.handle_input("initiate sacred communion")
    assert context_tracker.state.in_call is True

    orch.route("hello", {"emotion": "calm"}, voice_modality=True)

    assert connector.calls == ["/tmp/calm.wav"]
