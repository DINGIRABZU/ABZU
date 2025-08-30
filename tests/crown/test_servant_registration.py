"""Tests for crown servant registration."""

from __future__ import annotations

__version__ = "0.0.0"

import logging
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies used by init_crown_agent
sys.modules.setdefault("yaml", ModuleType("yaml"))
sys.modules.setdefault("vector_memory", ModuleType("vector_memory"))
sys.modules.setdefault("INANNA_AI.corpus_memory", ModuleType("corpus_memory"))

import INANNA_AI.glm_integration as gi
import init_crown_agent
import servant_model_manager as smm


def test_crown_servant_registration(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type(
        "R",
        (),
        {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}},
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


def test_servant_models_env(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type(
        "R",
        (),
        {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}},
    )()
    dummy.RequestException = Exception

    monkeypatch.setattr(gi, "requests", dummy)
    monkeypatch.setattr(init_crown_agent, "requests", dummy)

    smm._REGISTRY.clear()
    monkeypatch.setenv("SERVANT_MODELS", "alpha=http://a,beta=http://b")
    init_crown_agent.initialize_crown()
    models = smm.list_models()
    assert set(["alpha", "beta"]).issubset(models)


def test_servant_models_validation(monkeypatch, tmp_path, caplog):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type(
        "R",
        (),
        {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}},
    )()
    dummy.RequestException = Exception

    monkeypatch.setattr(gi, "requests", dummy)
    monkeypatch.setattr(init_crown_agent, "requests", dummy)

    smm._REGISTRY.clear()
    caplog.set_level(logging.WARNING)
    monkeypatch.setenv(
        "SERVANT_MODELS",
        "alpha=http://a,brokenpair,beta=http://b,alpha=http://c",
    )
    init_crown_agent.initialize_crown()
    models = smm.list_models()
    assert set(["alpha", "beta"]) == set(models)
    assert any("Skipping malformed SERVANT_MODELS entry" in m for m in caplog.messages)
    assert any("Duplicate servant model name" in m for m in caplog.messages)


def test_servant_models_requires_valid_pair(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("", encoding="utf-8")
    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda f: {}, raising=False)

    monkeypatch.setattr(init_crown_agent, "CONFIG_FILE", cfg)
    monkeypatch.setattr(init_crown_agent, "_check_glm", lambda i: None)

    dummy = ModuleType("requests")
    dummy.post = lambda *a, **k: type(
        "R",
        (),
        {"raise_for_status": lambda self: None, "json": lambda self: {"text": "pong"}},
    )()
    dummy.RequestException = Exception

    monkeypatch.setattr(gi, "requests", dummy)
    monkeypatch.setattr(init_crown_agent, "requests", dummy)

    smm._REGISTRY.clear()
    monkeypatch.setenv("SERVANT_MODELS", "brokenpair")
    with pytest.raises(SystemExit):
        init_crown_agent.initialize_crown()
