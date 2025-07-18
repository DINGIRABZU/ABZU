import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
import importlib

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
                sum(a * b for a, b in zip(e, q)) /
                ((_norm(e) * _norm(q)) + 1e-8)
                for e, _ in self.records
            ]
            order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[:n_results]
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
