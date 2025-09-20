"""Tests for corpus memory."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import corpus_memory
from tests.fixtures.chroma_baseline import stub_chromadb


def test_cli_search(tmp_path, monkeypatch, capsys):
    dirs = []
    for name in ["INANNA_AI", "GENESIS", "IGNITION", "QNL_LANGUAGE", "github"]:
        d = tmp_path / name
        d.mkdir()
        dirs.append(d)
    (dirs[1] / "found.md").write_text("A magical unicorn appears.", encoding="utf-8")
    (dirs[0] / "other.md").write_text("Nothing to see here.", encoding="utf-8")

    monkeypatch.setattr(corpus_memory, "MEMORY_DIRS", dirs)
    monkeypatch.setattr(corpus_memory, "CHROMA_DIR", tmp_path / "chroma")

    class DummyModel:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts, convert_to_numpy=True):
            def vec(t):
                return np.array([t.lower().count("unicorn")], dtype=float)

            if isinstance(texts, list):
                return np.array([vec(t) for t in texts])
            return vec(texts)

    monkeypatch.setattr(
        corpus_memory, "SentenceTransformer", lambda name: DummyModel(name)
    )
    monkeypatch.setattr(corpus_memory, "_HAVE_SENTENCE_TRANSFORMER", True)

    fake_chroma = stub_chromadb(monkeypatch, corpus_memory)

    assert corpus_memory.reindex_corpus()

    monkeypatch.setattr(
        corpus_memory.vector_memory,
        "search",
        lambda q, filter=None, k=10: [
            {"text": "A magical unicorn appears.", "tone": ""}
        ],
    )

    argv_backup = sys.argv.copy()
    sys.argv = ["corpus_memory", "--search", "unicorn", "--top", "1"]
    try:
        corpus_memory.main()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out.lower()
    assert "magical unicorn" in out

    assert fake_chroma.clients
    client = next(iter(fake_chroma.clients.values()))
    collection = client.collections.get("corpus")
    assert collection is not None
    assert any(
        rec["metadata"].get("path", "").endswith("found.md")
        for rec in collection.records
    )


def test_cli_reindex_runs(monkeypatch):
    called = {"reindex": False}

    def dummy_reindex():
        called["reindex"] = True
        return True

    monkeypatch.setattr(corpus_memory, "reindex_corpus", dummy_reindex)

    argv_backup = sys.argv.copy()
    sys.argv = ["corpus_memory", "--reindex"]
    try:
        corpus_memory.main()
    finally:
        sys.argv = argv_backup

    assert called["reindex"]


def test_cli_reindex_with_search(monkeypatch):
    called = {"reindex": False, "search": False}

    monkeypatch.setattr(
        corpus_memory,
        "reindex_corpus",
        lambda: called.__setitem__("reindex", True) or True,
    )
    monkeypatch.setattr(
        corpus_memory,
        "search_corpus",
        lambda *a, **k: called.__setitem__("search_corpus", True) or [("p", "s")],
    )
    monkeypatch.setattr(
        corpus_memory,
        "search",
        lambda *a, **k: called.__setitem__("search", True)
        or [{"text": "x", "tone": ""}],
    )

    argv_backup = sys.argv.copy()
    sys.argv = ["corpus_memory", "--reindex", "--search", "hello"]
    try:
        corpus_memory.main()
    finally:
        sys.argv = argv_backup

    assert called["reindex"] and called["search"]


def test_reindex_delete_failure(monkeypatch, tmp_path, caplog):
    d = tmp_path / "INANNA_AI"
    d.mkdir()
    (d / "a.md").write_text("text", encoding="utf-8")
    monkeypatch.setattr(corpus_memory, "MEMORY_DIRS", [d])
    monkeypatch.setattr(corpus_memory, "CHROMA_DIR", tmp_path / "chroma")

    class DummyModel:
        def __init__(self, name):
            pass

        def encode(self, texts, convert_to_numpy=True):  # type: ignore[no-untyped-def]
            return [[0.0] for _ in texts]

    monkeypatch.setattr(
        corpus_memory, "SentenceTransformer", lambda name: DummyModel(name)
    )
    monkeypatch.setattr(corpus_memory, "_HAVE_SENTENCE_TRANSFORMER", True)

    fake_chroma = stub_chromadb(monkeypatch, corpus_memory)

    def failing(name: str) -> None:
        raise RuntimeError("delete failed")

    original_pc = fake_chroma.PersistentClient

    def wrapped_pc(path: str | Path):
        client = original_pc(path)
        client.delete_collection = failing  # type: ignore[assignment]
        return client

    monkeypatch.setattr(fake_chroma, "PersistentClient", wrapped_pc)

    with caplog.at_level(logging.WARNING):
        ok = corpus_memory.reindex_corpus()
    assert ok is False
    assert "Failed to delete collection" in caplog.text
