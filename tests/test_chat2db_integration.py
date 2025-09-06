"""Integration test for Chat2DB combining SQLite and vector layers."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace

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


def _norm(v):
    return sum(i * i for i in v) ** 0.5


dummy_np.linalg = SimpleNamespace(norm=_norm)
sys.modules.setdefault("numpy", dummy_np)

import numpy as np

# stub qnl_utils used by spiral_vector_db
sys.modules.setdefault("MUSIC_FOUNDATION", ModuleType("MUSIC_FOUNDATION"))
qnl_mod = ModuleType("qnl_utils")
qnl_mod.quantum_embed = lambda text: (
    np.array([1.0, 0.0]) if "hello" in text else np.array([0.0, 1.0])
)
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qnl_mod)

from INANNA_AI import db_storage


def test_chat2db_integration(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIRAL_VECTOR_PATH", str(tmp_path / "vec"))
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

    db_path = tmp_path / "chat.db"
    db_storage.init_db(db_path=db_path)
    svdb.init_db(tmp_path / "vec")

    db_storage.save_interaction("hello world", "joy", "response.wav", db_path=db_path)
    svdb.insert_embeddings([{"text": "hello world", "label": "greeting"}])

    history = db_storage.fetch_interactions(db_path=db_path)
    assert history and history[0]["transcript"] == "hello world"

    matches = svdb.query_embeddings("hello", top_k=1)
    assert matches and matches[0]["label"] == "greeting"
