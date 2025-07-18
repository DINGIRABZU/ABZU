import sys
from types import ModuleType
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies used by init_crown_agent
sys.modules.setdefault("yaml", ModuleType("yaml"))
sys.modules.setdefault("vector_memory", ModuleType("vector_memory"))
sys.modules.setdefault("INANNA_AI.corpus_memory", ModuleType("corpus_memory"))

import init_crown_agent
import servant_model_manager as smm
import INANNA_AI.glm_integration as gi


def test_crown_servant_registration(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml
    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type(
        "R", (), {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}}
    )()
    dummy.RequestException = Exception

    monkeypatch.setattr(gi, "requests", dummy)
    monkeypatch.setattr(init_crown_agent, "requests", dummy)

    smm._REGISTRY.clear()
    monkeypatch.setenv("DEEPSEEK_URL", "http://ds")
    monkeypatch.setenv("MISTRAL_URL", "http://ms")
    monkeypatch.setenv("KIMI_K2_URL", "http://k2")

    init_crown_agent.initialize_crown()
    models = smm.list_models()
    assert set(["deepseek", "mistral", "kimi_k2"]).issubset(models)
