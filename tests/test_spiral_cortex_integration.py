import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("requests", types.ModuleType("requests"))
np_mod = types.ModuleType("numpy")
np_mod.ndarray = object
np_mod.float32 = float
np_mod.int16 = "int16"
np_mod.random = types.SimpleNamespace(rand=lambda *a, **k: 0)
sys.modules.setdefault("numpy", np_mod)

import recursive_emotion_router as rer
import cortex_memory
import archetype_feedback_loop as afl
import archetype_shift_engine


@dataclass
class TextNode:
    """Simple spiral node built from text."""

    text: str
    emotion: str = "joy"
    event: str = ""
    children: list["TextNode"] = field(default_factory=list)

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
        return {"emotion": self.emotion, "event": self.event or self.text}


def test_full_cycle_records_and_evaluates(tmp_path, monkeypatch):
    log_file = tmp_path / "cortex.jsonl"
    monkeypatch.setattr(cortex_memory, "CORTEX_MEMORY_FILE", log_file)
    monkeypatch.setattr(rer.vector_memory, "add_vector", lambda *a, **k: None)

    node = TextNode("invoke ritual")
    decision = rer.route(node)

    assert decision["event"] == "invoke ritual"
    data = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(data) == 1
    entry = json.loads(data[0])
    state = json.loads(entry["state"])
    assert state["text"] == "invoke ritual"

    monkeypatch.setattr(
        archetype_shift_engine,
        "maybe_shift_archetype",
        lambda event, emotion: "citrinitas_layer",
    )
    suggestion = afl.evaluate_archetype(limit=1)
    assert suggestion == "citrinitas_layer"
