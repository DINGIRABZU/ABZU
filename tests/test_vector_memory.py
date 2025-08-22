from __future__ import annotations

import importlib
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
qlm_mod = ModuleType("qnl_utils")
setattr(qlm_mod, "quantum_embed", lambda t: np.array([0.0]))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", qlm_mod)

import vector_memory


def test_add_and_search(monkeypatch, tmp_path):
    records = []

    class DummyCollection:
        def add(self, ids, embeddings, metadatas):
            for e, m in zip(embeddings, metadatas):
                records.append((np.asarray(e, dtype=float), m))

        def query(self, query_embeddings, n_results, **_):
            q = np.asarray(query_embeddings[0], dtype=float)
            sims = [
                float(e @ q / ((np.linalg.norm(e) * np.linalg.norm(q)) + 1e-8))
                for e, _ in records
            ]
            order = np.argsort(sims)[::-1][:n_results]
            return {
                "embeddings": [[records[i][0].tolist() for i in order]],
                "metadatas": [[records[i][1] for i in order]],
            }

    class DummyClient:
        def __init__(self, path):
            self.col = DummyCollection()

        def get_or_create_collection(self, name):
            return self.col

    dummy_chroma = SimpleNamespace(PersistentClient=lambda path: DummyClient(path))

    monkeypatch.setattr(vector_memory, "chromadb", dummy_chroma)
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)

    def fake_embed(text):
        return np.array([len(text), text.count("b")], dtype=float)

    monkeypatch.setattr(vector_memory.qnl_utils, "quantum_embed", fake_embed)

    now = datetime.utcnow()
    vector_memory.add_vector(
        "aaaa", {"emotion": "joy", "timestamp": (now - timedelta(days=1)).isoformat()}
    )
    vector_memory.add_vector("aaa", {"emotion": "joy", "timestamp": now.isoformat()})
    vector_memory.add_vector("bbb", {"emotion": "sad", "timestamp": now.isoformat()})

    res = vector_memory.search("aaaaa", filter={"emotion": "joy"}, k=2)
    assert [r["text"] for r in res] == ["aaa", "aaaa"]


def test_rewrite_vector_delete_failure(monkeypatch, caplog):
    class DummyCollection:
        def get(self, ids):
            return {"metadatas": [[{}]]}

        def update(self, ids, embeddings, metadatas):
            raise RuntimeError("update failed")

        def delete(self, ids):
            raise RuntimeError("delete failed")

        def add(self, ids, embeddings, metadatas):
            pass

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    monkeypatch.setattr(vector_memory.qnl_utils, "quantum_embed", lambda t: np.zeros(1))
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError):
            vector_memory.rewrite_vector("old", "new")
    assert "Failed to delete vector old" in caplog.text
