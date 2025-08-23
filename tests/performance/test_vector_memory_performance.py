"""Tests for vector memory performance."""

from __future__ import annotations

import importlib
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

vector_memory = importlib.import_module("vector_memory")


def test_vector_memory_search_performance(monkeypatch):
    monkeypatch.setattr(vector_memory, "np", None, raising=False)
    monkeypatch.setattr(
        vector_memory.qnl_utils, "quantum_embed", lambda text: [1.0, 0.0, 0.5]
    )

    class DummyCollection:
        def query(self, query_embeddings, n_results):
            embeddings = [[1.0, float(i), 0.5] for i in range(n_results)]
            metas = [
                {"timestamp": "2024-01-01T00:00:00", "text": f"t{i}"}
                for i in range(n_results)
            ]
            return {"embeddings": [embeddings], "metadatas": [metas]}

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    start = time.perf_counter()
    results = vector_memory.search("query", k=100)
    duration = time.perf_counter() - start
    assert len(results) == 100
    assert duration < 0.5
