"""Ensure reindex embeds Marrow Code and Inanna Song."""

from __future__ import annotations

import types

from INANNA_AI import corpus_memory


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

    # Stub chromadb client
    class DummyCollection:
        def __init__(self) -> None:
            self.ids: list[str] = []

        def add(self, ids, embeddings, metadatas):  # noqa: D401 - simple stub
            self.ids.extend(ids)

    class DummyClient:
        def __init__(self, path: str) -> None:
            self.collection = DummyCollection()

        def delete_collection(self, name: str) -> None:  # noqa: D401 - simple stub
            self.collection = DummyCollection()

        def create_collection(
            self, name: str
        ) -> DummyCollection:  # noqa: D401 - simple stub
            self.collection = DummyCollection()
            return self.collection

    shared_client = DummyClient("dummy")
    dummy_chroma = types.SimpleNamespace(PersistentClient=lambda path: shared_client)
    monkeypatch.setattr(corpus_memory, "chromadb", dummy_chroma)
    monkeypatch.setattr(corpus_memory, "_HAVE_CHROMADB", True)

    assert corpus_memory.reindex_corpus()
    ids = shared_client.collection.ids
    assert any(p.endswith("MARROW_CODE.md") for p in ids)
    assert any(p.endswith("INANNA_SONG.md") for p in ids)
