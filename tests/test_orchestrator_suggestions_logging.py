import sys
from pathlib import Path
import types
import logging

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub optional dependencies before importing the module
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sf_mod = sys.modules["soundfile"]
setattr(sf_mod, "write", lambda path, data, sr, subtype=None: Path(path).touch())

scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
scipy_mod.io = scipy_io
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.signal", signal_mod)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)

# Stub SPIRAL_OS dependencies
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", types.ModuleType("symbolic_parser"))
sb3_mod = types.ModuleType("stable_baselines3")
sb3_mod.PPO = lambda *a, **k: object()
sys.modules.setdefault("stable_baselines3", sb3_mod)

import orchestrator
from orchestrator import MoGEOrchestrator


def test_suggestions_logged_and_returned(monkeypatch, caplog, capsys):
    orch = MoGEOrchestrator()
    orch._interaction_count = 19
    monkeypatch.setattr(orchestrator.learning_mutator, "propose_mutations", lambda insights: ["alpha"])
    monkeypatch.setattr(orchestrator, "update_insights", lambda entries: None)
    monkeypatch.setattr(orchestrator, "load_insights", lambda: {})
    monkeypatch.setattr(orch._memory_logger, "load_interactions", lambda: [])
    monkeypatch.setattr(orch._task_profiler, "classify", lambda text: "task")
    monkeypatch.setattr(orch._model_selector, "choose", lambda *a, **k: "glm")
    monkeypatch.setattr(orch._model_selector, "model_from_emotion", lambda emotion: "glm")
    monkeypatch.setattr(orchestrator.vector_memory, "add_vector", lambda *a, **k: None)
    monkeypatch.setattr(orchestrator.vector_memory, "query_vectors", lambda *a, **k: [])

    with caplog.at_level(logging.INFO, logger="orchestrator"):
        result = orch.route(
            "hi",
            {"emotion": "joy"},
            text_modality=False,
            voice_modality=False,
            music_modality=False,
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert result["suggestions"] == ["alpha"]
    assert any(
        isinstance(r.msg, dict) and r.msg.get("suggestion") == "alpha"
        for r in caplog.records
    )
