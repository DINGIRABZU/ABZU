"""Tests for rag engine."""

from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path
from typing import Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _reload(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    if "rag.engine" in sys.modules:
        del sys.modules["rag.engine"]
    return importlib.import_module("rag.engine")


def test_query_filters_and_scores(monkeypatch):
    mod = _reload(monkeypatch)

    called = {}

    def fake_search(text, filter=None, k=5):
        called["args"] = (text, filter, k)
        data = [
            {"text": "A", "tag": "x", "score": 0.9},
            {"text": "B", "tag": "y", "score": 0.8},
        ]
        if filter:
            data = [r for r in data if all(r.get(k) == v for k, v in filter.items())]
        return data

    monkeypatch.setattr(mod, "vm_search", fake_search)

    res = mod.query("hello", filters={"tag": "x"}, top_n=2)

    assert called["args"] == ("hello", {"tag": "x"}, 2)
    assert len(res) == 1
    item = res[0]
    if isinstance(item, dict):
        assert item["snippet"] == "A"
        assert abs(item["score"] - 0.9) < 1e-6
    else:
        text = getattr(
            item, "content", getattr(getattr(item, "node", None), "text", "")
        )
        score = getattr(item, "score", 0.0)
        assert text == "A"
        assert abs(score - 0.9) < 1e-6


def test_cli_prints_results(monkeypatch, capsys):
    mod = _reload(monkeypatch)

    monkeypatch.setattr(
        mod,
        "vm_search",
        lambda *a, **k: [{"text": "hi", "score": 1.0}],
    )

    mod.main(["--query", "ping"])
    out = capsys.readouterr().out
    assert "hi" in out


@pytest.mark.parametrize(
    ("flag", "module", "exc"),
    [
        ("_HAYSTACK_AVAILABLE", "haystack", RuntimeError("haystack missing")),
        (
            "_LLAMA_AVAILABLE",
            "llama_index.core.schema",
            RuntimeError("llama missing"),
        ),
    ],
)
def test_missing_optional_dep_logs_warning(
    monkeypatch,
    caplog,
    flag: str,
    module: str,
    exc: Optional[Exception],
):
    mod = _reload(monkeypatch)
    setattr(mod, flag, True)

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == module:
            raise exc
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with caplog.at_level("WARNING"):
        mod._make_item("foo", {}, 1.0)

    assert str(exc) in caplog.text
