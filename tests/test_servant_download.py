"""Verify servant model registration via download CLI."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import servant_model_manager as smm


@pytest.mark.parametrize(
    "cli_arg, name, func_name",
    [
        ("deepseek", "deepseek", "download_deepseek"),
        ("mistral_8x22b", "mistral", "download_mistral_8x22b"),
        ("kimi_k2", "kimi_k2", "download_kimi_k2"),
    ],
)
def test_servant_registration(monkeypatch, cli_arg, name, func_name):
    module = importlib.import_module("download_models")
    smm._REGISTRY.clear()

    def _register(*args, **kwargs):
        smm.register_model(name, lambda prompt: f"{name}:{prompt}")

    monkeypatch.setattr(module, func_name, _register)
    argv = sys.argv.copy()
    sys.argv = ["download_models.py", cli_arg]
    try:
        module.main()
        assert smm.has_model(name)
    finally:
        sys.argv = argv
        smm._REGISTRY.clear()
