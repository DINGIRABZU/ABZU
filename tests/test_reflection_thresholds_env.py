import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import types

dummy_vm = types.ModuleType("vector_memory")
sys.modules.setdefault("vector_memory", dummy_vm)
sys.modules.setdefault("requests", types.ModuleType("requests"))
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))

from tools import reflection_loop


def test_load_thresholds_uses_env(tmp_path, monkeypatch):
    cfg = tmp_path / "custom.json"
    cfg.write_text('{"env": 0.7}')
    monkeypatch.setenv("MIRROR_THRESHOLDS_PATH", str(cfg))

    thresholds = reflection_loop.load_thresholds()

    assert thresholds == {"env": 0.7}
