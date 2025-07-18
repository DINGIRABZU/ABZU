import importlib
import sys
import types
from pathlib import Path

# stub heavy dependencies potentially imported by orchestrator
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
dummy_np = types.ModuleType("numpy")
dummy_np.asarray = lambda x, dtype=None: x
dummy_np.linalg = types.SimpleNamespace(norm=lambda x: 1.0)
sys.modules.setdefault("numpy", dummy_np)
qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
qlm_mod.quantum_embed = lambda t: [0.0]
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)
sys.modules.setdefault("MUSIC_FOUNDATION", types.ModuleType("MUSIC_FOUNDATION"))
sys.modules["MUSIC_FOUNDATION"].qnl_utils = qlm_mod

# Provide a lightweight orchestrator before importing crown_router
orch_mod = types.ModuleType("orchestrator")

class DummyOrchestrator:
    def route(self, *a, **k):
        return {"model": "glm"}

orch_mod.MoGEOrchestrator = DummyOrchestrator
sys.modules.setdefault("orchestrator", orch_mod)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_expression_memory_influences_choice(monkeypatch):
    import crown_router
    importlib.reload(crown_router)

    # MoGEOrchestrator is provided by the stub module above
    monkeypatch.setattr(crown_router.emotional_state, "get_soul_state", lambda: "awakened")
    monkeypatch.setattr(
        crown_router,
        "decide_expression_options",
        lambda e: {"tts_backend": "gtts", "avatar_style": "Plain", "aura": None},
    )

    records_a = [
        {
            "type": "expression_decision",
            "emotion": "joy",
            "tts_backend": "coqui",
            "avatar_style": "Soprano",
            "soul_state": "awakened",
        }
    ] * 2
    monkeypatch.setattr(crown_router.vector_memory, "search", lambda *a, **k: records_a)

    res = crown_router.route_decision("hi", {"emotion": "joy"})
    assert res["tts_backend"] == "coqui"
    assert res["avatar_style"] == "Soprano"

    records_b = [
        {
            "type": "expression_decision",
            "emotion": "joy",
            "tts_backend": "gtts",
            "avatar_style": "Baritone",
            "soul_state": "awakened",
        }
    ] * 2
    monkeypatch.setattr(crown_router.vector_memory, "search", lambda *a, **k: records_b)

    res2 = crown_router.route_decision("hi", {"emotion": "joy"})
    assert res2["tts_backend"] == "gtts"
    assert res2["avatar_style"] == "Baritone"

