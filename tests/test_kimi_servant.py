import asyncio
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import servant_model_manager as smm
from tools import kimi_k2_client


def test_register_kimi_servant(monkeypatch):
    smm._REGISTRY.clear()
    called = {}
    def dummy(prompt):
        called["prompt"] = prompt
        return "reply"

    monkeypatch.setattr(kimi_k2_client, "complete", dummy)
    smm.register_kimi_k2()
    assert smm.has_model("kimi_k2")
    out = asyncio.run(smm.invoke("kimi_k2", "hi"))
    assert out == "reply"
    assert called["prompt"] == "hi"
