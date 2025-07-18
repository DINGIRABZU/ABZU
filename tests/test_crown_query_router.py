import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

dummy_np = types.ModuleType("numpy")

class NPArray(list):
    def tolist(self):
        return list(self)

def _arr(x, dtype=None):
    return NPArray(x)

dummy_np.array = _arr
dummy_np.asarray = _arr
dummy_np.linalg = types.SimpleNamespace(norm=lambda v: sum(i * i for i in v) ** 0.5)
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

import crown_query_router as cqr
import rag_retriever


def test_route_query_selects_store(monkeypatch):
    called = {}
    def fake_retrieve(q, top_n=5, collection="tech"):
        called["store"] = collection
        return []

    monkeypatch.setattr(rag_retriever, "retrieve_top", fake_retrieve)

    cqr.route_query("what is quantum code?", "Sage")
    assert called["store"] == "tech"

    cqr.route_query("sing a song", "Jester")
    assert called["store"] == "music"
