import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import rag_embedder


class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[float(len(t))] for t in texts]


def test_embed_chunks_sentiment(monkeypatch):
    monkeypatch.setattr(rag_embedder, "SentenceTransformer", lambda name: DummyModel())
    rag_embedder._MODEL = None
    chunks = [
        {"text": "I love this", "source_path": "a", "archetype": "alpha"},
        {"text": "bad day", "source_path": "b"},
    ]
    res = rag_embedder.embed_chunks(chunks)
    assert res[0]["sentiment"] == "positive"
    assert res[0]["archetype"] == "alpha"
    assert res[1]["sentiment"] == "negative"
    assert isinstance(res[0]["embedding"], list)


def test_cli_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(rag_embedder, "SentenceTransformer", lambda name: DummyModel())
    rag_embedder._MODEL = None
    data = [{"text": "good", "source_path": "a"}]
    inp = tmp_path / "in.json"
    outp = tmp_path / "out.jsonl"
    inp.write_text(json.dumps(data), encoding="utf-8")
    rag_embedder.main(["--in", str(inp), "--out", str(outp)])
    lines = outp.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["sentiment"] == "positive"
    assert isinstance(rec["embedding"], list)
