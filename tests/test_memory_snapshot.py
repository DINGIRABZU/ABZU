"""Tests for memory snapshot."""

from __future__ import annotations

import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state
import vector_memory


def test_emotional_state_snapshot_restore(tmp_path, monkeypatch):
    monkeypatch.setattr(emotional_state, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(emotional_state, "REGISTRY_FILE", tmp_path / "reg.json")
    monkeypatch.setattr(emotional_state, "EVENT_LOG", tmp_path / "events.jsonl")
    emotional_state._STATE.clear()
    emotional_state._REGISTRY.clear()
    emotional_state.set_last_emotion("joy")
    emotional_state.set_resonance_level(0.5)
    snap = tmp_path / "snap.json"
    emotional_state.snapshot(snap)
    emotional_state.set_last_emotion("sad")
    emotional_state.set_resonance_level(0.1)
    emotional_state.restore(snap)
    assert emotional_state.get_last_emotion() == "joy"
    assert emotional_state.get_resonance_level() == 0.5


def test_vector_memory_snapshot_restore(tmp_path, monkeypatch):
    class DummyCollection:
        def __init__(self):
            self.data = {"ids": [], "embeddings": [], "metadatas": []}

        def add(self, ids, embeddings, metadatas):
            if isinstance(ids, list):
                self.data["ids"].extend(ids)
                self.data["embeddings"].extend(embeddings)
                self.data["metadatas"].extend(metadatas)
            else:
                self.data["ids"].append(ids)
                self.data["embeddings"].append(embeddings)
                self.data["metadatas"].append(metadatas)

        def get(self, ids=None):
            if ids is None:
                return self.data
            res = {"ids": [], "embeddings": [], "metadatas": []}
            for i in ids:
                idx = self.data["ids"].index(i)
                for key in res:
                    res[key].append(self.data[key][idx])
            return res

        def delete(self, ids):
            for i in ids:
                idx = self.data["ids"].index(i)
                for key in self.data:
                    self.data[key].pop(idx)

    col = DummyCollection()
    monkeypatch.setattr(vector_memory, "_COLLECTION", col)
    monkeypatch.setattr(vector_memory, "_get_collection", lambda: col)
    monkeypatch.setattr(vector_memory, "_EMBED", lambda s: [1.0, 0.0])
    monkeypatch.setattr(vector_memory, "_DIR", tmp_path)

    vector_memory.add_vector("hello", {})
    snap = tmp_path / "vm.json"
    vector_memory.snapshot(snap)

    manifest = tmp_path / "snapshots" / "manifest.json"
    assert manifest.exists()
    assert str(snap) in json.loads(manifest.read_text())

    col.data = {"ids": [], "embeddings": [], "metadatas": []}
    vector_memory.restore(snap)
    assert col.data["metadatas"][0]["text"] == "hello"
