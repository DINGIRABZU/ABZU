import sys
from pathlib import Path
import types

dummy_np = types.ModuleType("numpy")


class NPArray(list):
    def tolist(self):
        return list(self)

    def __matmul__(self, other):
        return sum(a * b for a, b in zip(self, other))

    def flatten(self):
        return self


def _arr(x, dtype=None):
    return NPArray(x)


dummy_np.array = _arr
dummy_np.asarray = _arr
dummy_np.linalg = types.SimpleNamespace(norm=lambda v: sum(i * i for i in v) ** 0.5)
dummy_np.clip = lambda val, lo, hi: lo if val < lo else hi if val > hi else val
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rag_parser
import rag_embedder
import rag_retriever
import crown_query_router


class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[1.0, 0.0] if "hello" in t else [0.0, 1.0] for t in texts]


class DummyCollection:
    def __init__(self):
        self.records = []

    def add(self, ids, embeddings, metadatas):
        for emb, meta in zip(embeddings, metadatas):
            self.records.append((emb, meta))

    def query(self, query_embeddings, n_results, **_):
        q = query_embeddings[0]
        sims = [float(sum(a * b for a, b in zip(e, q))) for e, _ in self.records]
        order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[:n_results]
        return {
            "embeddings": [[self.records[i][0] for i in order]],
            "metadatas": [[self.records[i][1] for i in order]],
        }


def test_spiral_rag_pipeline(tmp_path, monkeypatch):
    base = tmp_path / "inputs"
    base.mkdir()
    f = base / "doc.txt"
    f.write_text("hello world", encoding="utf-8")

    chunks = rag_parser.load_inputs(base)
    monkeypatch.setattr(rag_embedder, "SentenceTransformer", lambda name: DummyModel())
    rag_embedder._MODEL = None
    embedded = rag_embedder.embed_chunks(chunks)

    col = DummyCollection()
    monkeypatch.setattr(rag_retriever, "get_collection", lambda name: col)
    monkeypatch.setattr(rag_retriever.rag_embedder, "_get_model", lambda: DummyModel())

    col.add(["1"], [embedded[0]["embedding"]], [{k: v for k, v in embedded[0].items() if k != "embedding"}])

    res = crown_query_router.route_query("hello", "Sage")
    assert res
    assert res[0]["text"] == "hello world"
    assert res[0]["source_path"] == str(f)
