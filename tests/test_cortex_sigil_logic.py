import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
ql_stub = ModuleType("qnl_utils")
setattr(ql_stub, "quantum_embed", lambda t: [0.0])
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ql_stub)

import cortex_sigil_logic as csl
import recursive_emotion_router as rer


class DummyNode:
    def __init__(self, event=""):
        self.event = event
        self.children = []

    def ask(self):
        pass

    def feel(self):
        pass

    def symbolize(self):
        pass

    def pause(self):
        pass

    def reflect(self):
        pass

    def decide(self):
        return {"event": self.event}


def test_interpret_sigils():
    assert csl.interpret_sigils("hello 🜂") == ["anger"]
    assert csl.interpret_sigils("none") == []


def test_router_sigil_integration(monkeypatch):
    node = DummyNode("do 🜁")
    monkeypatch.setattr(rer.vector_memory, "add_vector", lambda *a, **k: None)
    monkeypatch.setattr(rer.cortex_memory, "record_spiral", lambda *a, **k: None)

    res = rer.route(node)

    assert res["sigil_triggers"] == ["calm"]
