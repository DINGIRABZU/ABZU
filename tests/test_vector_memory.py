"""Tests for vector memory."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace
import json

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


def test_persist_and_restore_snapshot(monkeypatch, tmp_path):
    class DummyStore:
        def __init__(self):
            self.restored = None

        def snapshot(self, path):  # type: ignore[no-untyped-def]
            Path(path).write_text("snap", encoding="utf-8")

        def restore(self, path):  # type: ignore[no-untyped-def]
            self.restored = Path(path)

    store = DummyStore()
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    monkeypatch.setattr(vector_memory, "_get_collection", lambda: store)

    snap_path = vector_memory.persist_snapshot()
    assert snap_path.exists()
    assert vector_memory.restore_latest_snapshot()
    assert store.restored == snap_path


def test_persist_clusters(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    monkeypatch.setattr(
        vector_memory,
        "cluster_vectors",
        lambda k=5, limit=1000: [{"cluster": 0, "count": 1}],
    )

    path = vector_memory.persist_clusters()
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == [{"cluster": 0, "count": 1}]

    manifest = tmp_path / "snapshots" / "clusters_manifest.json"
    assert manifest.exists()
    assert str(path) in json.loads(manifest.read_text(encoding="utf-8"))

    assert vector_memory.load_latest_clusters() == data


def test_optional_vector_memory_noops(monkeypatch):
    optional_vm = pytest.importorskip("memory.optional.vector_memory")

    sentinel_meta = {"id": 1, "tags": ["edge", "case"]}
    # The optional module should tolerate arbitrary arguments and simply
    # discard data without raising exceptions.
    assert optional_vm.query_vectors("text", limit=5, filter=sentinel_meta) == []
    assert optional_vm.search("question", filter=sentinel_meta, k=3) == []

    # Even persistence-flavoured arguments should be ignored gracefully.
    assert optional_vm.add_vector("payload", sentinel_meta, persist=True) is None
