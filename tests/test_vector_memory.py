"""Tests for vector memory."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
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

    monkeypatch.setattr(vector_memory, "chromadb", dummy_chroma, raising=False)
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
    class DummyStore:
        def __init__(self) -> None:
            self.metadata = {"old": {}}

        def rewrite(self, old_id, emb_list, meta):  # type: ignore[no-untyped-def]
            raise RuntimeError("update failed")

    store = DummyStore()
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    monkeypatch.setattr(vector_memory, "_DIST", None)
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)
    monkeypatch.setattr(vector_memory, "_log", lambda *a, **k: None)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [0.0])
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError):
            vector_memory.rewrite_vector("old", "new")
    assert "update failed" in caplog.text


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

    restored: list[Path] = []
    monkeypatch.setattr(
        vector_memory, "restore", lambda path: restored.append(Path(path))
    )

    assert vector_memory.restore_latest_snapshot()
    assert restored and restored[0] == snap_path


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


def test_configure_requires_distributed(monkeypatch):
    monkeypatch.setattr(vector_memory, "DistributedMemory", None)
    with pytest.raises(RuntimeError):
        vector_memory.configure(redis_url="redis://localhost:6379/0")


def test_add_vector_retries_with_legacy_signature(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    monkeypatch.setattr(vector_memory, "_DIST", None)
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)
    monkeypatch.setattr(vector_memory, "_log", lambda *a, **k: None)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [1.0, 2.0])

    class DummyCollection:
        def __init__(self):
            self.calls: list[tuple[Any, Any, Any]] = []

        def add(self, ids, embeddings, metadatas):  # type: ignore[no-untyped-def]
            self.calls.append((ids, embeddings, metadatas))
            if len(self.calls) == 1:
                raise TypeError("needs sequences")

    dummy = DummyCollection()
    monkeypatch.setattr(vector_memory, "_get_collection", lambda: dummy)

    vector_memory.add_vector("payload", {"kind": "test"})
    first, second = dummy.calls
    assert isinstance(first[0], str)
    assert isinstance(second[0], list)
    assert second[0][0] == first[0]


def test_search_uses_native_search(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [1.0, 0.0])
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)

    class DummyCollection:
        def search(self, query, k):  # type: ignore[no-untyped-def]
            assert query == [1.0, 0.0]
            now = datetime.utcnow().isoformat()
            return [
                (
                    "keep",
                    [1.0, 0.0],
                    {"timestamp": now, "tag": "yes", "text": "stored"},
                ),
                (
                    "drop",
                    [0.0, 1.0],
                    {"timestamp": now, "tag": "no", "text": "ignored"},
                ),
            ]

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    monkeypatch.setattr(vector_memory, "_DIST", None)
    results = vector_memory.search(
        "query", filter={"tag": "yes"}, k=1, scoring="similarity"
    )
    assert len(results) == 1
    assert results[0]["tag"] == "yes"
    assert results[0]["text"] == "stored"
    assert 0 <= results[0]["score"] <= 1


def test_rewrite_vector_updates_store(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    monkeypatch.setattr(vector_memory, "_DIST", None)
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)
    monkeypatch.setattr(vector_memory, "_log", lambda *a, **k: None)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [0.5, 0.5])

    class DummyStore:
        def __init__(self):
            self.metadata = {"old": {"extra": "value"}}
            self.rewrites: list[tuple[str, Any, dict]] = []

        def rewrite(self, old_id, emb_list, meta):  # type: ignore[no-untyped-def]
            self.rewrites.append((old_id, emb_list, meta))

    store = DummyStore()
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)

    assert vector_memory.rewrite_vector("old", "new text")
    assert store.rewrites
    _, embedding, meta = store.rewrites[-1]
    assert meta["text"] == "new text"
    assert meta["extra"] == "value"
    assert isinstance(embedding, list)


def test_restore_latest_snapshot_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    assert vector_memory.restore_latest_snapshot() is False
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    bad = snap_dir / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        vector_memory,
        "restore",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert vector_memory.restore_latest_snapshot() is False


def test_compact_removes_stale_entries(monkeypatch):
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)

    class DummyStore:
        def __init__(self):
            old = datetime.utcnow() - timedelta(days=10)
            self.metadata = {
                "stale": {"timestamp": old.isoformat()},
                "fresh": {"timestamp": datetime.utcnow().isoformat()},
            }
            self.deleted: list[list[str]] = []

        def delete(self, ids):  # type: ignore[no-untyped-def]
            self.deleted.append(list(ids))

    store = DummyStore()
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    vector_memory._compact(0.5)
    assert store.deleted and store.deleted[0] == ["stale"]


def test_snapshot_without_native_support(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)
    monkeypatch.setattr(vector_memory, "_log_narrative", lambda *a, **k: None)

    class DummyCollection:
        def get(self):  # type: ignore[no-untyped-def]
            return {
                "ids": ["a"],
                "embeddings": [[0.1, 0.2]],
                "metadatas": [[{"text": "a"}]],
            }

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    out_path = tmp_path / "snapshot.json"
    vector_memory.snapshot(out_path)
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["ids"] == ["a"]
    manifest = tmp_path / "snapshots" / "manifest.json"
    assert manifest.exists()
