"""Tests for vector memory."""

from __future__ import annotations

import logging
import sqlite3
import sys
import threading
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


def test_embed_and_similarity_without_numpy(monkeypatch):
    monkeypatch.setattr(vector_memory, "np", None, raising=False)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [1.0, 2.0])

    emb = vector_memory.embed_text("phrase")
    assert emb == [1.0, 2.0]

    sim = vector_memory.cosine_similarity([1, 0], [1, 0])
    assert sim == pytest.approx(1.0)


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


def test_configure_with_distributed_and_shards(monkeypatch, tmp_path):
    class DummyDist:
        def __init__(self, url, client=None):
            self.url = url
            self.client = client

        def restore_to(self, store):  # type: ignore[no-untyped-def]
            store.restored = True

        def backup(self, *_a, **_k):  # type: ignore[no-untyped-def]
            return None

    class DummyStore:
        def __init__(self, dir_path, shards=1, snapshot_interval=1):
            self.db_path = Path(dir_path) / "memory.sqlite"
            self.snapshot_interval = snapshot_interval
            self.metadata: dict[str, dict[str, Any]] = {}
            self.ids: list[str] = []
            self._stores = [SimpleNamespace(db_path=self.db_path)] * shards
            self.restored = False

        def snapshot(self, target):  # type: ignore[no-untyped-def]
            self.snapshot_target = target

    monkeypatch.setattr(vector_memory, "DistributedMemory", DummyDist)
    monkeypatch.setattr(vector_memory, "_MemoryStore", DummyStore)
    monkeypatch.setattr(vector_memory, "ShardedMemoryStore", DummyStore)
    started: list[bool] = []
    monkeypatch.setattr(
        vector_memory, "_start_compaction_thread", lambda: started.append(True)
    )
    monkeypatch.setattr(vector_memory, "_DIST", None, raising=False)
    vector_memory.configure(
        db_path=tmp_path / "vm",
        embedder=lambda text: [len(text)],
        redis_url="redis://example",
        shards=2,
        snapshot_interval=2,
        decay_strategy="linear",
        decay_seconds=10.0,
        compaction_interval=0.1,
        decay_threshold=0.4,
    )
    store = vector_memory._get_store()
    assert isinstance(store, DummyStore)
    assert getattr(store, "restored", False)
    assert vector_memory._DECAY_STRATEGY == "linear"
    assert started


def test_vacuum_files_invokes_sqlite(monkeypatch, tmp_path):
    store = SimpleNamespace(
        db_path=tmp_path / "main.sqlite",
        _stores=[SimpleNamespace(db_path=tmp_path / "shard.sqlite")],
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    executed: list[str] = []

    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, sql):
            executed.append(sql)

    monkeypatch.setattr(sqlite3, "connect", lambda path: DummyConn())
    vector_memory._vacuum_files()
    assert "VACUUM" in executed[0]


def test_after_write_triggers_snapshot(monkeypatch, tmp_path):
    snapshots: list[Path] = []
    store = SimpleNamespace(
        _stores=[SimpleNamespace()],
        snapshot=lambda target: snapshots.append(Path(target)),
    )
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    monkeypatch.setattr(vector_memory, "_SNAPSHOT_INTERVAL", 1, raising=False)
    monkeypatch.setattr(vector_memory, "_OP_COUNT", 0, raising=False)
    vector_memory._after_write()
    assert snapshots and snapshots[0] == tmp_path / "snapshots"


def test_after_write_snapshot_without_shards(monkeypatch, tmp_path):
    snapshots: list[Path] = []

    def _snapshot(target: Path) -> None:
        snapshots.append(target)

    store = SimpleNamespace(snapshot=_snapshot)
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    monkeypatch.setattr(vector_memory, "_SNAPSHOT_INTERVAL", 1, raising=False)
    monkeypatch.setattr(vector_memory, "_OP_COUNT", 0, raising=False)

    vector_memory._after_write()

    assert snapshots == [tmp_path / "snapshots" / "memory.sqlite"]


def test_add_vectors_batches(monkeypatch):
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        vector_memory, "add_vector", lambda text, meta: calls.append((text, meta))
    )
    vector_memory.add_vectors(["a", "b"], [{"x": 1}, {"y": 2}])
    assert calls == [("a", {"x": 1}), ("b", {"y": 2})]


def test_decay_modes(monkeypatch):
    monkeypatch.setattr(vector_memory, "_DECAY_STRATEGY", "none", raising=False)
    assert vector_memory._decay("not-a-date") == 1.0
    now = datetime.utcnow().isoformat()
    assert vector_memory._decay(now) == 1.0
    monkeypatch.setattr(vector_memory, "_DECAY_STRATEGY", "linear", raising=False)
    monkeypatch.setattr(vector_memory, "_DECAY_SECONDS", 2.0, raising=False)
    ts = (datetime.utcnow() - timedelta(seconds=1)).isoformat()
    linear = vector_memory._decay(ts)
    assert 0.0 < linear <= 1.0
    monkeypatch.setattr(vector_memory, "_DECAY_STRATEGY", "exponential", raising=False)
    assert vector_memory._decay(ts) < 1.0


def test_search_with_collection_search(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [1.0, 0.0])

    class DummyCollection:
        def search(self, query, k):  # type: ignore[no-untyped-def]
            now = datetime.utcnow().isoformat()
            return [
                (
                    "keep",
                    [1.0, 0.0],
                    {"timestamp": now, "tag": "yes", "text": "hello"},
                ),
                (
                    "skip",
                    [0.0, 1.0],
                    {"timestamp": now, "tag": "no", "text": "ignored"},
                ),
            ]

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    monkeypatch.setattr(vector_memory, "_DIST", None, raising=False)
    results = vector_memory.search(
        "query", filter={"tag": "yes"}, k=1, scoring="recency"
    )
    assert results and results[0]["text"] == "hello"


def test_search_without_numpy(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "np", None, raising=False)
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [1.0, 0.0])

    class DummyCollection:
        def search(self, query, k):  # type: ignore[no-untyped-def]
            now = datetime.utcnow().isoformat()
            return [("only", [1.0, 0.0], {"timestamp": now, "text": "entry"})]

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())

    results = vector_memory.search("query", k=1, scoring="hybrid")
    assert results and results[0]["text"] == "entry"


def test_search_batch(monkeypatch):
    monkeypatch.setattr(vector_memory, "search", lambda q, **kw: [q])
    assert vector_memory.search_batch(["a", "b"], k=1) == [["a"], ["b"]]


def test_rewrite_vector_with_distributed(monkeypatch):
    rewrites: list[tuple[str, list[float], dict[str, Any]]] = []
    store = SimpleNamespace(
        metadata={"old": {"extra": "value"}},
        rewrite=lambda oid, emb, meta: rewrites.append((oid, emb, meta)),
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)

    class DummyDist:
        def __init__(self):
            self.ids: list[str] = []

        def backup(self, id_, emb, meta):  # type: ignore[no-untyped-def]
            self.ids.append(id_)

    monkeypatch.setattr(vector_memory, "_DIST", DummyDist(), raising=False)
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)
    monkeypatch.setattr(vector_memory, "_log", lambda *a, **k: None)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda text: [0.1, 0.2])
    assert vector_memory.rewrite_vector("old", "new text")
    assert rewrites and rewrites[0][0] == "old"
    assert vector_memory._DIST.ids == ["old"]  # type: ignore[attr-defined]


def test_query_vectors_filters(monkeypatch):
    store = SimpleNamespace(
        metadata={
            "keep": {"timestamp": "1", "tag": "yes"},
            "drop": {"timestamp": "2", "tag": "no"},
        }
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    res = vector_memory.query_vectors(filter={"tag": "yes"}, limit=5)
    assert res == [{"timestamp": "1", "tag": "yes", "id": "keep"}]


def test_compactor_waits_for_interval(monkeypatch):
    deletes: list[list[str]] = []
    store = SimpleNamespace(
        metadata={
            "stale": {"timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat()}
        },
        delete=lambda ids: deletes.append(list(ids)),
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    monkeypatch.setattr(vector_memory, "_after_write", lambda: None)
    monkeypatch.setattr(vector_memory, "_DECAY_THRESHOLD", 0.5, raising=False)
    waits: list[float] = []

    class DummyStop:
        def __init__(self):
            self.calls = 0

        def is_set(self):
            self.calls += 1
            return self.calls > 1

        def wait(self, interval):
            waits.append(interval)

    monkeypatch.setattr(vector_memory, "_COMPACTION_STOP", DummyStop(), raising=False)
    monkeypatch.setattr(vector_memory, "_COMPACTION_INTERVAL", 0.01, raising=False)
    vector_memory._compactor()
    assert deletes and waits


def test_start_compaction_thread(monkeypatch):
    vector_memory._COMPACTION_THREAD = SimpleNamespace(is_alive=lambda: True)
    vector_memory._start_compaction_thread()
    started: list[bool] = []

    class DummyThread:
        def __init__(self, *a, **k):
            pass

        def start(self):
            started.append(True)

        def is_alive(self):
            return True

    vector_memory._COMPACTION_THREAD = None
    monkeypatch.setattr(
        vector_memory,
        "_COMPACTION_STOP",
        SimpleNamespace(clear=lambda: None),
        raising=False,
    )
    monkeypatch.setattr(threading, "Thread", lambda *a, **k: DummyThread(*a, **k))
    vector_memory._start_compaction_thread()
    assert started


def test_snapshot_with_native_snapshot(monkeypatch, tmp_path):
    outputs: list[Path] = []

    class DummyCollection:
        def snapshot(self, path):  # type: ignore[no-untyped-def]
            outputs.append(Path(path))

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(vector_memory, "_log_narrative", lambda *a, **k: None)
    vector_memory.snapshot(tmp_path / "native.json")
    assert outputs == [tmp_path / "native.json"]


def test_restore_directory_with_restore_method(monkeypatch, tmp_path):
    snap_dir = tmp_path / "snap"
    snap_dir.mkdir()
    db_location = snap_dir / "memory.sqlite"
    db_location.write_text("data", encoding="utf-8")
    restores: list[Path] = []

    class DummyCollection:
        db_path = db_location

        def restore(self, path):  # type: ignore[no-untyped-def]
            restores.append(Path(path))

    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    vector_memory.restore(snap_dir)
    assert restores == [db_location]


def test_persist_snapshot_normalizes_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    manifest = snap_dir / "manifest.json"
    manifest.write_text(
        json.dumps([str(tmp_path / "snapshots" / "old" / "memory.sqlite.bak")]),
        encoding="utf-8",
    )
    store = SimpleNamespace(
        _stores=[],
        snapshot=lambda target: Path(target).write_text("{}", encoding="utf-8"),
        db_path=str(tmp_path / "memory.sqlite"),
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)
    result = vector_memory.persist_snapshot()
    assert result.exists()


def test_restore_latest_snapshot_success(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    latest = snap_dir / "20240101000000"
    latest.mkdir()
    data = {"ids": [], "embeddings": [], "metadatas": []}
    (latest / "data.json").write_text(json.dumps(data), encoding="utf-8")

    class DummyCollection:
        def get(self):
            return {"ids": []}

        def delete(self, ids):  # type: ignore[no-untyped-def]
            return None

        def add(self, ids, embeddings, metadatas):  # type: ignore[no-untyped-def]
            added.extend(ids)

    added: list[Any] = []
    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    assert vector_memory.restore_latest_snapshot()
    assert added == []


def test_cluster_vectors_with_stub(monkeypatch):
    store = SimpleNamespace(
        metadata={"a": {"text": "aa"}, "b": {"text": "bb"}}, index=None
    )
    monkeypatch.setattr(vector_memory, "_get_store", lambda: store)

    def _embed(text: str):
        if text.startswith("a"):
            return np.array([1.0, 0.0], dtype=float)
        return np.array([0.0, 1.0], dtype=float)

    monkeypatch.setattr(vector_memory, "_EMBED", _embed)

    class DummyKmeans:
        def __init__(self, dim, k, niter, verbose):
            pass

        def train(self, arr):
            return None

        @property
        def index(self):
            class Index:
                def search(self, arr, k):
                    return None, np.array([[0], [1]])

            return Index()

    monkeypatch.setattr(
        vector_memory,
        "faiss",
        SimpleNamespace(Kmeans=lambda *a, **k: DummyKmeans(*a, **k)),
    )
    res = vector_memory.cluster_vectors(k=2, limit=2)
    assert sorted(c["count"] for c in res) == [1, 1]


def test_persist_clusters_with_path(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    monkeypatch.setattr(
        vector_memory,
        "cluster_vectors",
        lambda k=5, limit=1000: [{"cluster": 0, "count": 2}],
    )
    target = tmp_path / "clusters.json"
    out_path = vector_memory.persist_clusters(path=target)
    assert out_path == target
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == [{"cluster": 0, "count": 2}]


def test_load_latest_clusters_edge_cases(monkeypatch, tmp_path):
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path, raising=False)
    snap_dir = tmp_path / "snapshots"
    snap_dir.mkdir()
    manifest = snap_dir / "clusters_manifest.json"
    manifest.write_text(json.dumps([]), encoding="utf-8")
    assert vector_memory.load_latest_clusters() == []
    manifest.write_text("not json", encoding="utf-8")
    assert vector_memory.load_latest_clusters() == []
