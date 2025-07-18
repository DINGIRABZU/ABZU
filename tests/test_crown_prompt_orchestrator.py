import sys
from pathlib import Path
import types

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
dummy_np.mean = lambda arr: sum(arr) / len(arr)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crown_prompt_orchestrator import crown_prompt_orchestrator
import servant_model_manager as smm
import crown_decider


class DummyGLM:
    def __init__(self):
        self.seen = None

    def complete(self, prompt: str, quantum_context: str | None = None) -> str:
        self.seen = prompt
        return f"glm:{prompt}"


def test_basic_flow(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        "crown_prompt_orchestrator.load_interactions",
        lambda limit=3: [{"input": "hi"}],
    )
    result = crown_prompt_orchestrator("hello", glm)
    assert result["text"].startswith("glm:")
    assert result["model"] == "glm"
    assert "hi" in glm.seen
    assert result["state"] == "dormant"


def test_servant_invocation(monkeypatch):
    glm = DummyGLM()
    smm.register_model("deepseek", lambda p: f"ds:{p}")
    monkeypatch.setattr(
        crown_decider, "recommend_llm", lambda t, e: "deepseek"
    )
    result = crown_prompt_orchestrator("how do things work?", glm)
    assert result["text"] == "ds:how do things work?"
    assert result["model"] == "deepseek"


def test_state_engine_integration(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        "crown_prompt_orchestrator.load_interactions",
        lambda limit=3: [],
    )
    result = crown_prompt_orchestrator("begin the ritual", glm)
    assert result["state"] == "ritual"


def test_empty_interactions_response(monkeypatch):
    glm = DummyGLM()
    monkeypatch.setattr(
        "crown_prompt_orchestrator.load_interactions",
        lambda limit=3: [],
    )
    result = crown_prompt_orchestrator("hello", glm)
    assert result["text"].startswith("glm:")
    assert "<no interactions>" in glm.seen


def test_technical_prefers_kimi(monkeypatch):
    glm = DummyGLM()
    smm._REGISTRY.clear()
    smm.register_model("kimi_k2", lambda p: f"k2:{p}")
    monkeypatch.setattr(
        "crown_prompt_orchestrator.load_interactions",
        lambda limit=3: [],
    )
    monkeypatch.setattr(crown_decider, "recommend_llm", lambda t, e: "kimi_k2")
    result = crown_prompt_orchestrator("import os", glm)
    assert result["text"] == "k2:import os"
    assert result["model"] == "kimi_k2"

