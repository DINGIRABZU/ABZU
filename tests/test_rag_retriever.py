import sys
from pathlib import Path
import types

dummy_np = types.ModuleType("numpy")

class NPArray(list):
    def tolist(self):
        return list(self)

    def __matmul__(self, other):
        return sum(a * b for a, b in zip(self, other))

def _arr(x, dtype=None):
    return NPArray(x)

dummy_np.array = _arr
dummy_np.asarray = _arr
dummy_np.linalg = types.SimpleNamespace(norm=lambda v: sum(i * i for i in v) ** 0.5)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rag_retriever


class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[1.0, 0.0] if "foo" in t else [0.0, 1.0] for t in texts]


class DummyCollection:
    def __init__(self):
        self.records = [
            (np.array([1.0, 0.0]), {"snippet": "A"}),
            (np.array([0.0, 1.0]), {"snippet": "B"}),
        ]

    def query(self, query_embeddings, n_results, **_):
        q = np.asarray(query_embeddings[0])
        sims = [float(e @ q / ((np.linalg.norm(e) * np.linalg.norm(q)) + 1e-8)) for e, _ in self.records]
        order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[:n_results]
        return {
            "embeddings": [[self.records[i][0] for i in order]],
            "metadatas": [[self.records[i][1] for i in order]],
        }


def test_retrieve_top_ranks(monkeypatch):
    monkeypatch.setattr(rag_retriever.rag_embedder, "_get_model", lambda: DummyModel())
    monkeypatch.setattr(rag_retriever, "get_collection", lambda name: DummyCollection())

    res = rag_retriever.retrieve_top("foo question", top_n=2, collection="tech")

    assert [r["snippet"] for r in res] == ["A", "B"]
    assert res[0]["score"] >= res[1]["score"]
