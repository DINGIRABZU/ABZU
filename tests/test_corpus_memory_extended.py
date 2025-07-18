import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import corpus_memory


def test_add_entry_logs_and_stores(monkeypatch, tmp_path):
    added = {}

    def dummy_add_vector(text, metadata):
        added['text'] = text
        added['meta'] = metadata

    log_calls = {}

    monkeypatch.setattr(corpus_memory.vector_memory, "add_vector", dummy_add_vector)
    monkeypatch.setattr(
        corpus_memory,
        "corpus_memory_logging",
        type(
            "L",
            (),
            {"log_interaction": lambda *a, **k: log_calls.setdefault("logged", True)},
        ),
    )

    meta = corpus_memory.add_entry("hello", "joy")
    assert added["text"] == "hello"
    assert added["meta"]["tone"] == "joy"
    assert meta["text"] == "hello"
    assert log_calls.get("logged")


def test_search_filters_and_orders(monkeypatch):
    dummy_results = [
        {"text": "foo", "tone": "joy", "score": 0.9},
        {"text": "baz", "tone": "joy", "score": 0.8},
        {"text": "bar", "tone": "calm", "score": 0.5},
    ]

    def dummy_search(query, filter=None, k=5):
        assert filter == {"tone": "joy"}
        return dummy_results

    monkeypatch.setattr(corpus_memory.vector_memory, "search", dummy_search)

    res = corpus_memory.search("hello!", emotion="joy", similarity_threshold=0.1)
    assert [r["text"] for r in res] == ["foo", "baz", "bar"][: len(res)]


def test_prioritize_by_tone():
    items = [
        {"text": "a", "tone": "calm"},
        {"text": "b", "tone": "joy"},
        {"text": "c", "tone": "joy"},
    ]
    out = corpus_memory.prioritize_by_tone(items, "joy")
    assert [i["text"] for i in out[:2]] == ["b", "c"]

