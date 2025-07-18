import sys
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import corpus_memory
import types


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

    monkeypatch.setattr(corpus_memory, "SentenceTransformer", lambda name: DummyModel(name))

    class DummyCollection:
        def __init__(self) -> None:
            self.ids = []
            self.embeddings = []

        def add(self, ids, embeddings, metadatas):
            self.ids.extend(ids)
            self.embeddings.extend([np.array(e) for e in embeddings])

        def query(self, query_embeddings, n_results):
            q = np.array(query_embeddings[0])
            sims = [float(e @ q / ((np.linalg.norm(e) * np.linalg.norm(q)) + 1e-8)) for e in self.embeddings]
            order = np.argsort(sims)[::-1][:n_results]
            return {"ids": [[self.ids[i] for i in order]]}

    class DummyClient:
        def __init__(self, path):
            self.collection = DummyCollection()

        def get_or_create_collection(self, name):
            return self.collection

        def create_collection(self, name):
            self.collection = DummyCollection()
            return self.collection

        def delete_collection(self, name):
            self.collection = DummyCollection()

    shared_client = DummyClient("dummy")
    dummy_chroma = types.SimpleNamespace(PersistentClient=lambda path: shared_client)
    monkeypatch.setattr(corpus_memory, "chromadb", dummy_chroma)

    corpus_memory.reindex_corpus()

    monkeypatch.setattr(
        corpus_memory.vector_memory,
        "search",
        lambda q, filter=None, k=10: [{"text": "A magical unicorn appears.", "tone": ""}],
    )

    argv_backup = sys.argv.copy()
    sys.argv = ["corpus_memory", "--search", "unicorn", "--top", "1"]
    try:
        corpus_memory.main()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out.lower()
    assert "magical unicorn" in out


def test_cli_reindex_runs(monkeypatch):
    called = {"reindex": False}

    def dummy_reindex():
        called["reindex"] = True

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

    monkeypatch.setattr(corpus_memory, "reindex_corpus", lambda: called.__setitem__("reindex", True))
    monkeypatch.setattr(
        corpus_memory,
        "search_corpus",
        lambda *a, **k: called.__setitem__("search_corpus", True) or [("p", "s")],
    )
    monkeypatch.setattr(
        corpus_memory,
        "search",
        lambda *a, **k: called.__setitem__("search", True) or [{"text": "x", "tone": ""}],
    )

    argv_backup = sys.argv.copy()
    sys.argv = ["corpus_memory", "--reindex", "--search", "hello"]
    try:
        corpus_memory.main()
    finally:
        sys.argv = argv_backup

    assert called["reindex"] and called["search"]
