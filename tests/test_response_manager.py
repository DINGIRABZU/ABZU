import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import response_manager, corpus_memory


def test_generate_reply_queries_corpus(monkeypatch):
    calls = {}

    def fake_search(query: str, top_k: int = 3, dirs=None, model_name="all-MiniLM-L6-v2"):
        calls['query'] = query
        return [("path", "snippet text")]

    monkeypatch.setattr(corpus_memory, "search_corpus", fake_search)

    mgr = response_manager.ResponseManager()
    info = {"emotion": "excited", "classification": "speech"}
    reply = mgr.generate_reply("hello", info)
    assert "snippet text" in reply
    assert "excited" in calls['query']
    assert "speech" in calls['query']
    assert "excited" in reply
    assert "speech" in reply
