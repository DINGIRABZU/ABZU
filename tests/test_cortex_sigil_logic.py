import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
ql_stub = ModuleType("qnl_utils")
setattr(ql_stub, "quantum_embed", lambda t: [0.0])
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ql_stub)

import recursive_emotion_router as rer
from labs import cortex_sigil as csl


class DummyNode:
    def __init__(self, event=""):
        self.event = event
        self.children = []
        self.calls = []

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
        return {"event": self.event}


def test_interpret_sigils():
    assert csl.interpret_sigils("hello 🜂") == ["anger"]
    assert csl.interpret_sigils("none") == []


def test_interpret_multiple_sigils():
    """Order and duplicates should be preserved when multiple sigils appear."""
    text = "🜂🜁🜂"
    assert csl.interpret_sigils(text) == ["anger", "calm", "anger"]


def test_router_sigil_integration(monkeypatch):
    node = DummyNode("do 🜁")
    stages: list[str] = []

    def add_vector(_, meta):
        stages.append(meta["stage"])

    logged = []

    def record_spiral(node, result):
        logged.append((node, result))

    monkeypatch.setattr(rer.vector_memory, "add_vector", add_vector)
    monkeypatch.setattr(rer.cortex_memory, "record_spiral", record_spiral)

    res = rer.route(node)

    # All stages should have been invoked in order on the node
    assert (
        node.calls
        == list(stages)
        == [
            "ask",
            "feel",
            "symbolize",
            "pause",
            "reflect",
            "decide",
        ]
    )
    # Cortex memory should receive the final decision with sigil triggers
    assert logged and logged[0][1]["sigil_triggers"] == ["calm"]


def test_router_without_sigil(monkeypatch):
    """Routing text lacking sigils should not produce trigger metadata."""

    node = DummyNode("plain text")
    stages: list[str] = []

    def add_vector(_, meta):
        stages.append(meta["stage"])

    logged = []

    def record_spiral(node, result):
        logged.append((node, result))

    monkeypatch.setattr(rer.vector_memory, "add_vector", add_vector)
    monkeypatch.setattr(rer.cortex_memory, "record_spiral", record_spiral)

    res = rer.route(node)

    assert (
        node.calls
        == list(stages)
        == [
            "ask",
            "feel",
            "symbolize",
            "pause",
            "reflect",
            "decide",
        ]
    )
    assert logged and "sigil_triggers" not in logged[0][1]
