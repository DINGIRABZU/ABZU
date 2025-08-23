"""Tests for optional imports."""

from __future__ import annotations

import builtins
import importlib
import sys


def _fake_import(name, globals=None, locals=None, fromlist=(), level=0, missing=()):
    if name in missing:
        raise ImportError(name)
    return _real_import(name, globals, locals, fromlist, level)


_real_import = builtins.__import__


def test_adaptive_learning_import_without_optional_deps(monkeypatch):
    for mod in [
        "INANNA_AI.adaptive_learning",
        "stable_baselines3",
        "gymnasium",
        "numpy",
    ]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
    monkeypatch.setattr(
        builtins,
        "__import__",
        lambda name, *a, **k: _fake_import(
            name, *a, missing={"stable_baselines3", "gymnasium", "numpy"}, **k
        ),
    )
    importlib.import_module("INANNA_AI.adaptive_learning")


def test_sentence_transformer_modules_import(monkeypatch):
    missing = {"sentence_transformers"}
    monkeypatch.setattr(
        builtins,
        "__import__",
        lambda name, *a, **k: _fake_import(name, *a, missing=missing, **k),
    )
    monkeypatch.delitem(sys.modules, "sentence_transformers", raising=False)
    for mod in [
        "INANNA_AI.corpus_memory",
        "INANNA_AI.learning.github_scraper",
        "INANNA_AI.learning.project_gutenberg",
        "INANNA_AI.ethical_validator",
    ]:
        monkeypatch.delitem(sys.modules, mod, raising=False)
        importlib.import_module(mod)
