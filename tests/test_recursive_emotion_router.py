import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

# Ensure vector_memory dependency can be imported
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
qnl_stub = ModuleType("qnl_utils")
setattr(qnl_stub, "quantum_embed", lambda t: [0.0])
sys.modules.setdefault("SPIRAL_OS.qnl_utils", qnl_stub)

import recursive_emotion_router as rer


class DummyNode:
    def __init__(self):
        self.children = []
        self.steps = []

    def ask(self):
        self.steps.append("ask")

    def feel(self):
        self.steps.append("feel")

    def symbolize(self):
        self.steps.append("symbolize")

    def pause(self):
        self.steps.append("pause")

    def reflect(self):
        self.steps.append("reflect")

    def decide(self):
        self.steps.append("decide")
        return {"decision": len(self.steps)}


def test_route_logs_each_stage(monkeypatch):
    node = DummyNode()
    logged = []
    monkeypatch.setattr(rer.vector_memory, "add_vector", lambda t, m: logged.append(m["stage"]))

    res = rer.route(node)

    assert res == {"decision": 6}
    assert logged == ["ask", "feel", "symbolize", "pause", "reflect", "decide"]
    assert node.steps == logged


def test_recursive_depth(monkeypatch):
    root = DummyNode()
    child = DummyNode()
    root.children.append(child)

    logged = []
    monkeypatch.setattr(rer.vector_memory, "add_vector", lambda t, m: logged.append(m["stage"]))

    rer.route(root, depth=2)

    assert len(logged) == 12
    assert child.steps == ["ask", "feel", "symbolize", "pause", "reflect", "decide"]
