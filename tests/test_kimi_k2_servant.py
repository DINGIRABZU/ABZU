import sys
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide dummy modules to satisfy imports
sys.modules.setdefault("yaml", ModuleType("yaml"))
sys.modules.setdefault("vector_memory", ModuleType("vector_memory"))
sys.modules.setdefault("INANNA_AI.corpus_memory", ModuleType("corpus_memory"))

import init_crown_agent
import servant_model_manager as smm


def test_init_servants_registers_kimi_k2(monkeypatch):
    called = {}
    monkeypatch.setattr(smm, "register_kimi_k2", lambda: called.setdefault("ok", True))
    monkeypatch.setenv("KIMI_K2_URL", "http://host")
    init_crown_agent._init_servants({})
    assert called == {"ok": True}


def test_initialize_crown_registers_kimi(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml
    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type("R", (), {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}})()
    dummy.RequestException = Exception

    import INANNA_AI.glm_integration as gi
    monkeypatch.setattr(gi, "requests", dummy)

    smm._REGISTRY.clear()
    monkeypatch.setenv("KIMI_K2_URL", "http://host")
    init_crown_agent.initialize_crown()
    assert smm.has_model("kimi_k2")
