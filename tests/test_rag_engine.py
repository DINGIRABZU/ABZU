import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _reload(monkeypatch):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    if "rag_engine" in sys.modules:
        del sys.modules["rag_engine"]
    return importlib.import_module("rag_engine")


def test_query_filters_and_scores(monkeypatch):
    mod = _reload(monkeypatch)

    called = {}

    def fake_search(text, filter=None, k=5):
        called["args"] = (text, filter, k)
        return [
            {"text": "A", "tag": "x", "score": 0.9},
            {"text": "B", "tag": "y", "score": 0.8},
        ]

    monkeypatch.setattr(mod, "vm_search", fake_search)

    res = mod.query("hello", filters={"tag": "x"}, top_n=2)

    assert called["args"] == ("hello", {"tag": "x"}, 2)
    assert len(res) == 1
    item = res[0]
    if isinstance(item, dict):
        assert item["snippet"] == "A"
        assert abs(item["score"] - 0.9) < 1e-6
    else:
        text = getattr(item, "content", getattr(getattr(item, "node", None), "text", ""))
        score = getattr(item, "score", 0.0)
        assert text == "A"
        assert abs(score - 0.9) < 1e-6


def test_cli_prints_results(monkeypatch, capsys):
    mod = _reload(monkeypatch)

    monkeypatch.setattr(
        mod,
        "vm_search",
        lambda *a, **k: [{"text": "hi", "score": 1.0}],
    )

    mod.main(["--query", "ping"])
    out = capsys.readouterr().out
    assert "hi" in out
