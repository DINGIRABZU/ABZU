"""Ensure reindex embeds Marrow Code and Inanna Song."""

from __future__ import annotations

from INANNA_AI import corpus_memory
from tests.fixtures.chroma_baseline import stub_chromadb


def test_reindex_embeds_marrow_and_song(tmp_path, monkeypatch):
    # Create sample memory files
    (tmp_path / "MARROW_CODE.md").write_text("marrow", encoding="utf-8")
    (tmp_path / "INANNA_SONG.md").write_text("song", encoding="utf-8")

    # Point memory and chroma directories to the temporary location
    monkeypatch.setattr(corpus_memory, "MEMORY_DIRS", [tmp_path])
    chroma_dir = tmp_path / "chroma"
    monkeypatch.setattr(corpus_memory, "CHROMA_DIR", chroma_dir)

    # Stub SentenceTransformer and mark dependency available
    class DummyModel:
        def __init__(self, name: str) -> None:
            pass

        def encode(self, texts, convert_to_numpy=True):  # noqa: D401 - simple stub
            if isinstance(texts, list):
                return [[0.0] for _ in texts]
            return [[0.0]]

    monkeypatch.setattr(
        corpus_memory, "SentenceTransformer", lambda name: DummyModel(name)
    )
    monkeypatch.setattr(corpus_memory, "_HAVE_SENTENCE_TRANSFORMER", True)

    fake_chroma = stub_chromadb(monkeypatch, corpus_memory)
    monkeypatch.setattr(corpus_memory, "_HAVE_CHROMADB", True)

    assert corpus_memory.reindex_corpus()
    assert fake_chroma.clients
    client = next(iter(fake_chroma.clients.values()))
    collection = client.collections.get("corpus")
    assert collection is not None
    ids = [rec["id"] for rec in collection.records]
    assert any(p.endswith("MARROW_CODE.md") for p in ids)
    assert any(p.endswith("INANNA_SONG.md") for p in ids)
