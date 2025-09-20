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

from tests.fixtures.chroma_baseline import stub_chromadb

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
    fake_chroma = stub_chromadb(monkeypatch, svdb)
    monkeypatch.setattr(
        svdb.qnl_utils,
        "quantum_embed",
        lambda text: np.array([1.0, 0.0]) if "hello" in text else np.array([0.0, 1.0]),
    )
    svdb.np = None

    db_path = tmp_path / "chat.db"
    db_storage.init_db(db_path=db_path)
    svdb.init_db(tmp_path / "vec")

    db_storage.save_interaction("hello world", "joy", "response.wav", db_path=db_path)
    svdb.insert_embeddings([{"text": "hello world", "label": "greeting"}])

    history = db_storage.fetch_interactions(db_path=db_path)
    assert history and history[0]["transcript"] == "hello world"

    matches = svdb.query_embeddings("hello", top_k=1)
    assert matches and matches[0]["label"] == "greeting"

    collection = fake_chroma.get_collection(svdb.DB_PATH, "spiral_vectors")
    assert any(rec["metadata"].get("label") == "greeting" for rec in collection.records)
