import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory import cortex as cortex_memory


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
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)

    node = DummyNode("A")
    for method in ["ask", "feel", "symbolize", "pause", "reflect", "decide"]:
        getattr(node, method)()
    cortex_memory.record_spiral(node, {"emotion": "joy", "action": "run"})
    cortex_memory.record_spiral(node, {"emotion": "calm", "action": "rest"})

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert node.calls == ["ask", "feel", "symbolize", "pause", "reflect", "decide"]

    # append invalid line
    log_file.write_text(log_file.read_text(encoding="utf-8") + "{\n", encoding="utf-8")

    res = cortex_memory.query_spirals({"emotion": "joy"})
    assert len(res) == 1
    assert res[0]["decision"]["action"] == "run"
    assert "A" in res[0]["state"]

    all_entries = cortex_memory.query_spirals({})
    assert len(all_entries) == 2
    assert all_entries[1]["decision"]["action"] == "rest"
