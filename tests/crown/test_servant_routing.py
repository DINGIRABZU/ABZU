import asyncio
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
dummy_np = types.ModuleType("numpy")
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
dummy_np.mean = lambda arr: sum(arr) / len(arr) if arr else 0
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

import crown_prompt_orchestrator as cpo
import crown_decider
import servant_model_manager as smm


class DummyGLM:
    def complete(self, prompt: str, quantum_context: str | None = None) -> str:
        return f"glm:{prompt}"


def _run(message: str, task_type: str, monkeypatch) -> dict:
    smm._REGISTRY.clear()
    smm.register_model("opencode", lambda p: f"oc:{p}")
    monkeypatch.setattr(cpo, "load_interactions", lambda limit=3: [])
    monkeypatch.setattr(cpo, "classify_task", lambda msg: task_type)
    monkeypatch.setattr(
        crown_decider,
        "recommend_llm",
        lambda t, e: (_ for _ in ()).throw(AssertionError("decider used")),
    )
    glm = DummyGLM()
    return asyncio.run(cpo.crown_prompt_orchestrator_async(message, glm))


def test_repair_routes_to_opencode(monkeypatch):
    result = _run("fix bug", "repair", monkeypatch)
    assert result["model"] == "opencode"
    assert result["text"] == "oc:fix bug"


def test_refactor_routes_to_opencode(monkeypatch):
    result = _run("clean code", "refactor", monkeypatch)
    assert result["model"] == "opencode"
    assert result["text"] == "oc:clean code"
