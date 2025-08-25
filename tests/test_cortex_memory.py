"""Tests for cortex memory."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory import cortex as cortex_memory
import json
from concurrent.futures import ThreadPoolExecutor


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


def test_fulltext_and_concurrent_queries(tmp_path, monkeypatch):
    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("A")
    cortex_memory.record_spiral(node, {"emotion": "joy", "tags": ["fast runner"]})

    # full-text search
    ft_res = cortex_memory.query_spirals(text="runner")
    assert len(ft_res) == 1

    # concurrent queries
    requests = [{"tags": ["fast runner"]}, {"text": "runner"}]
    results = cortex_memory.query_spirals_concurrent(requests)
    assert results[0] == results[1]

    # concurrent record/query race
    def writer():
        for i in range(20):
            cortex_memory.record_spiral(node, {"action": f"a{i}", "tags": [f"tag{i}"]})

    def reader():
        for _ in range(20):
            cortex_memory.query_spirals(text="runner")

    with ThreadPoolExecutor() as ex:
        ex.submit(writer)
        ex.submit(reader)

    idx = json.loads(index_file.read_text(encoding="utf-8"))
    assert "_fulltext" in idx


def test_concurrent_reads_and_writes(tmp_path, monkeypatch):
    """Ensure simultaneous reads and writes remain consistent."""
    log_file = tmp_path / "spiral.jsonl"
    index_file = tmp_path / "index.json"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(cortex_memory, "CORTEX_INDEX_FILE", index_file)

    node = DummyNode("X")

    def writer(i: int) -> None:
        cortex_memory.record_spiral(
            node, {"num": i, "tags": [f"t{i}"]}
        )

    def reader(i: int) -> None:
        cortex_memory.query_spirals(tags=[f"t{i}"])

    with ThreadPoolExecutor(max_workers=10) as ex:
        for i in range(10):
            ex.submit(writer, i)
            ex.submit(reader, i)

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    for i in range(10):
        res = cortex_memory.query_spirals(tags=[f"t{i}"])
        assert res and res[0]["decision"]["num"] == i
