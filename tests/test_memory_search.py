import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))

from memory import search


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
