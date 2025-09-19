"""Tests for spiral vector db."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

# provide minimal numpy stub
dummy_np = ModuleType("numpy")


class NPArray(list):
    def tolist(self):
        return list(self)


def _arr(x, dtype=None):
    return NPArray(x)


dummy_np.array = _arr


def _asarray(x, dtype=None):
    return NPArray(x)


dummy_np.asarray = _asarray


def _argsort(arr):
    return sorted(range(len(arr)), key=lambda i: arr[i])


dummy_np.argsort = _argsort


def _norm(v):
    return sum(i * i for i in v) ** 0.5


dummy_np.linalg = SimpleNamespace(norm=_norm)
sys.modules.setdefault("numpy", dummy_np)

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("MUSIC_FOUNDATION", ModuleType("MUSIC_FOUNDATION"))
qlm_mod = ModuleType("qnl_utils")
qlm_mod.quantum_embed = lambda t: np.array([0.0])
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)


def test_insert_and_query(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIRAL_VECTOR_PATH", str(tmp_path / "db"))
    if "spiral_vector_db" in sys.modules:
        del sys.modules["spiral_vector_db"]
    svdb = importlib.import_module("spiral_vector_db")

    class DummyCollection:
        def __init__(self):
            self.records = []

        def add(self, ids, embeddings, metadatas):
            for e, m in zip(embeddings, metadatas):
                self.records.append((np.asarray(e), m))

        def query(self, query_embeddings, n_results, **_):
            q = np.asarray(query_embeddings[0])
            sims = [
                sum(a * b for a, b in zip(e, q)) / ((_norm(e) * _norm(q)) + 1e-8)
                for e, _ in self.records
            ]
            order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[
                :n_results
            ]
            return {
                "embeddings": [[self.records[i][0] for i in order]],
                "metadatas": [[self.records[i][1] for i in order]],
            }

    class DummyClient:
        def __init__(self, path):
            self.col = DummyCollection()

        def get_or_create_collection(self, name):
            return self.col

    dummy_chroma = SimpleNamespace(PersistentClient=lambda path: DummyClient(path))
    monkeypatch.setattr(svdb, "chromadb", dummy_chroma)
    monkeypatch.setattr(
        svdb.qnl_utils,
        "quantum_embed",
        lambda text: np.array([1.0, 0.0]) if "foo" in text else np.array([0.0, 1.0]),
    )

    svdb.init_db()
    assert (tmp_path / "db").exists()

    data = [
        {"id": "a", "embedding": [1.0, 0.0], "label": "foo"},
        {"id": "b", "embedding": [0.0, 1.0], "label": "bar"},
    ]
    svdb.insert_embeddings(data)

    res = svdb.query_embeddings("foo text", top_k=1, filters={"label": "foo"})
    assert len(res) == 1
    assert res[0]["label"] == "foo"


def test_insert_embeddings_without_vectors(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIRAL_VECTOR_PATH", str(tmp_path / "db2"))
    sys.modules.pop("spiral_vector_db", None)
    svdb = importlib.import_module("spiral_vector_db")

    class DummyCollection:
        def __init__(self) -> None:
            self.calls: list[tuple[list[str], list[list[float]], list[dict]]] = []

        def add(self, ids=None, embeddings=None, metadatas=None, **_):  # type: ignore[no-untyped-def]
            self.calls.append((ids, embeddings, metadatas))

    collection = DummyCollection()

    class DummyClient:
        def __init__(self, path):
            self.col = collection

        def get_or_create_collection(self, name):
            return self.col

    embed_calls: list[str] = []

    monkeypatch.setattr(
        svdb,
        "chromadb",
        SimpleNamespace(PersistentClient=lambda path: DummyClient(path)),
    )
    monkeypatch.setattr(
        svdb.qnl_utils,
        "quantum_embed",
        lambda text: embed_calls.append(text) or np.array([len(text)], dtype=float),
    )

    svdb.init_db()
    svdb.insert_embeddings(
        [
            {"id": "given", "embedding": [0.1], "label": "x"},
            {"text": "needs", "label": "y"},
        ]
    )

    assert embed_calls == ["needs"]
    ids, embeddings, metas = collection.calls[0]
    assert ids[0] == "given"
    assert metas[1]["label"] == "y"
    assert embeddings[1]


def test_query_embeddings_filters_and_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIRAL_VECTOR_PATH", str(tmp_path / "db3"))
    sys.modules.pop("spiral_vector_db", None)
    svdb = importlib.import_module("spiral_vector_db")
    svdb._COLLECTION = None

    class DummyCollection:
        def query(self, query_embeddings, n_results, **_):  # type: ignore[no-untyped-def]
            return {
                "embeddings": [[[], [1.0, 0.0]]],
                "metadatas": [[{"label": "skip"}, {"label": "keep"}]],
            }

    svdb._COLLECTION = DummyCollection()
    monkeypatch.setattr(
        svdb.qnl_utils, "quantum_embed", lambda text: np.array([1.0, 0.0], dtype=float)
    )
    results = svdb.query_embeddings("question", top_k=2, filters={"label": "keep"})
    assert results == [{"label": "keep", "score": pytest.approx(1.0)}]


def test_init_db_requires_chromadb(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIRAL_VECTOR_PATH", str(tmp_path / "db4"))
    sys.modules.pop("spiral_vector_db", None)
    svdb = importlib.import_module("spiral_vector_db")
    monkeypatch.setattr(svdb, "chromadb", None)
    with pytest.raises(RuntimeError):
        svdb.init_db()
