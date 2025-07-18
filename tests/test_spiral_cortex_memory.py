import sys
import json
from pathlib import Path
import types

# Stub heavy deps before import
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
dummy_np.ndarray = NPArray
dummy_np.float32 = float
dummy_np.clip = lambda x, a, b: max(a, min(b, x))
sys.modules.setdefault("numpy", dummy_np)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rag_retriever
import spiral_cortex_memory as scm
import ritual_trainer
import auto_retrain


class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[1.0, 0.0] if "foo" in t else [0.0, 1.0] for t in texts]


class DummyCollection:
    def __init__(self):
        self.records = [
            (dummy_np.array([1.0, 0.0]), {"snippet": "A"}),
            (dummy_np.array([0.0, 1.0]), {"snippet": "B"}),
        ]

    def query(self, query_embeddings, n_results, **_):
        q = dummy_np.asarray(query_embeddings[0])
        sims = [float(e @ q / ((dummy_np.linalg.norm(e) * dummy_np.linalg.norm(q)) + 1e-8)) for e, _ in self.records]
        order = list(reversed(sorted(range(len(sims)), key=lambda i: sims[i])))[:n_results]
        return {
            "embeddings": [[self.records[i][0] for i in order]],
            "metadatas": [[self.records[i][1] for i in order]],
        }


def test_retrieval_logs_insight(tmp_path, monkeypatch):
    log_file = tmp_path / "mem.jsonl"
    monkeypatch.setattr(scm, "INSIGHT_FILE", log_file)
    monkeypatch.setattr(rag_retriever, "spiral_cortex_memory", scm)
    monkeypatch.setattr(rag_retriever.rag_embedder, "_get_model", lambda: DummyModel())
    monkeypatch.setattr(rag_retriever, "get_collection", lambda n: DummyCollection())

    rag_retriever.retrieve_top("foo question", top_n=1, collection="tech")

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["question"] == "foo question"
    assert entry["snippets"][0]["snippet"] == "A"
    assert "sentiment" in entry


def test_trainer_triggers(tmp_path, monkeypatch):
    mem_file = tmp_path / "mem.jsonl"
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(scm, "INSIGHT_FILE", mem_file)
    monkeypatch.setattr(ritual_trainer, "STATE_FILE", state_file)
    monkeypatch.setattr(ritual_trainer, "THRESHOLD", 2)

    data = [
        {"question": "q1", "snippets": [{"snippet": "s1"}], "sentiment": 0.1},
        {"question": "q2", "snippets": [{"snippet": "s2"}], "sentiment": -0.1},
    ]
    with mem_file.open("w", encoding="utf-8") as fh:
        for d in data:
            fh.write(json.dumps(d))
            fh.write("\n")

    monkeypatch.setattr(auto_retrain, "system_idle", lambda: True)
    captured = {}
    monkeypatch.setattr(auto_retrain, "trigger_finetune", lambda ds: captured.setdefault("data", ds))

    ritual_trainer.run_training(True)

    assert len(captured.get("data", [])) == 2
    assert state_file.exists()
