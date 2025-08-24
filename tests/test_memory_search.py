"""Tests for memory search."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))

from memory import search  # noqa: E402


def test_query_all_combines_sources(monkeypatch):
    now = datetime.utcnow().isoformat()

    monkeypatch.setattr(
        search.cortex,
        "query_spirals",
        lambda: [{"timestamp": now, "state": "alpha memory"}],
    )

    class DummyMem:
        def _load_events(self, limit=50):
            return [("alpha spiral", None, None)]

    monkeypatch.setattr(search.spiral_memory, "DEFAULT_MEMORY", DummyMem())

    monkeypatch.setattr(
        search.vector_memory,
        "search",
        lambda text, k=5: [{"text": "alpha vector", "timestamp": now}],
    )

    res = search.query_all("alpha")
    sources = {r["source"] for r in res}
    assert sources == {"cortex", "spiral", "vector"}


def test_recency_weighting(monkeypatch):
    now = datetime.utcnow()
    old_ts = (now - timedelta(days=2)).isoformat()
    new_ts = now.isoformat()

    monkeypatch.setattr(search.cortex, "query_spirals", lambda: [])

    class DummyMem:
        def _load_events(self, limit=50):
            return []

    monkeypatch.setattr(search.spiral_memory, "DEFAULT_MEMORY", DummyMem())

    monkeypatch.setattr(
        search.vector_memory,
        "search",
        lambda text, k=5: [
            {"text": "old", "timestamp": old_ts},
            {"text": "new", "timestamp": new_ts},
        ],
    )

    res = search.query_all("irrelevant")
    assert [r["text"] for r in res] == ["new", "old"]


def test_cortex_exception_logs_warning(monkeypatch, caplog):
    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(search.cortex, "query_spirals", boom)

    class DummyMem:
        def _load_events(self, limit=50):
            return []

    monkeypatch.setattr(search.spiral_memory, "DEFAULT_MEMORY", DummyMem())
    monkeypatch.setattr(search.vector_memory, "search", lambda text, k=5: [])

    with caplog.at_level("WARNING"):
        search.query_all("test")

    assert any("cortex" in message for message in caplog.messages)


def test_spiral_exception_logs_warning(monkeypatch, caplog):
    monkeypatch.setattr(search.cortex, "query_spirals", lambda: [])

    class DummyMem:
        def _load_events(self, limit=50):
            raise RuntimeError("boom")

    monkeypatch.setattr(search.spiral_memory, "DEFAULT_MEMORY", DummyMem())
    monkeypatch.setattr(search.vector_memory, "search", lambda text, k=5: [])

    with caplog.at_level("WARNING"):
        search.query_all("test")

    assert any("spiral" in message for message in caplog.messages)


def test_vector_exception_logs_warning(monkeypatch, caplog):
    monkeypatch.setattr(search.cortex, "query_spirals", lambda: [])

    class DummyMem:
        def _load_events(self, limit=50):
            return []

    monkeypatch.setattr(search.spiral_memory, "DEFAULT_MEMORY", DummyMem())

    def boom(*args, **kwargs):  # noqa: ANN001, ANN002
        raise RuntimeError("boom")

    monkeypatch.setattr(search.vector_memory, "search", boom)

    with caplog.at_level("WARNING"):
        search.query_all("test")

    assert any("vector" in message for message in caplog.messages)
