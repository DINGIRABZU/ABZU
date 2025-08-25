"""Tests for cortex memory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory import cortex as cortex_memory
import json


class DummyNode:
    def __init__(self, val):
        self.val = val
        self.children = []
        self.calls: list[str] = []

    def ask(self):
        self.calls.append("ask")

    def feel(self):
        self.calls.append("feel")

    def symbolize(self):
        self.calls.append("symbolize")

    def pause(self):
        self.calls.append("pause")

    def reflect(self):
        self.calls.append("reflect")

    def decide(self):
        self.calls.append("decide")
        return {"action": self.val}


def test_record_and_query(tmp_path, monkeypatch):
    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("A")
    for method in ["ask", "feel", "symbolize", "pause", "reflect", "decide"]:
        getattr(node, method)()
    cortex_memory.record_spiral(node, {"emotion": "joy", "action": "run", "tags": ["fast", "happy"]})
    cortex_memory.record_spiral(node, {"emotion": "calm", "action": "rest", "tags": ["slow"]})

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert node.calls == ["ask", "feel", "symbolize", "pause", "reflect", "decide"]

    # append invalid line
    log_file.write_text(log_file.read_text(encoding="utf-8") + "{\n", encoding="utf-8")

    res = cortex_memory.query_spirals(filter={"emotion": "joy"})
    assert len(res) == 1
    assert res[0]["decision"]["action"] == "run"
    assert "A" in res[0]["state"]

    tag_res = cortex_memory.query_spirals(tags=["fast"])
    assert len(tag_res) == 1
    assert tag_res[0]["decision"]["action"] == "run"

    all_entries = cortex_memory.query_spirals(filter={})
    assert len(all_entries) == 2
    assert all_entries[1]["decision"]["action"] == "rest"

    export_path = tmp_path / "export.json"
    cortex_memory.export_spirals(export_path, tags=["fast"])
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported[0]["decision"]["action"] == "run"


def test_prune(tmp_path, monkeypatch):
    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("A")
    cortex_memory.record_spiral(node, {"emotion": "joy", "action": "run", "tags": ["keep"]})
    cortex_memory.record_spiral(node, {"emotion": "sad", "action": "cry", "tags": ["drop"]})
    cortex_memory.prune_spirals(1)

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    res = cortex_memory.query_spirals(tags=["keep"])
    assert len(res) == 1
    assert res[0]["decision"]["action"] == "run"
