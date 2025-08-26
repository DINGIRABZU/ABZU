import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import vector_memory


def _embed(text: str):
    return [float(len(text))]


def test_persistence_across_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(vector_memory, "_DIST", None)
    dbdir = tmp_path / "vm"
    vector_memory.configure(db_path=dbdir, embedder=_embed, snapshot_interval=1)
    vector_memory.add_vector("hello", {})
    snap = vector_memory.persist_snapshot()
    # remove primary database file to simulate restart without data
    for f in dbdir.glob("**/*.sqlite"):
        f.unlink()
    vector_memory.configure(db_path=dbdir, embedder=_embed, snapshot_interval=1)
    items = vector_memory.query_vectors(limit=10)
    assert any(i["text"] == "hello" for i in items)
    assert snap.exists()
