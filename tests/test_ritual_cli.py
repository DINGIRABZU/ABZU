import types
import json
import builtins
import sys
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Stub heavy dependencies
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
sys.modules["numpy"].int16 = "int16"
sys.modules["numpy"].float32 = float
sys.modules["numpy"].ndarray = object
scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
scipy_mod.io = scipy_io
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
sys.modules.setdefault("scipy.signal", signal_mod)
mod_sf = types.ModuleType("soundfile")
mod_sf.write = lambda *a, **k: None
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: object()
gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
gym_mod.spaces = types.SimpleNamespace(Box=lambda **k: None)
sys.modules.setdefault("stable_baselines3", stable_mod)
sys.modules.setdefault("gymnasium", gym_mod)
sys.modules.setdefault("soundfile", mod_sf)


start_path = ROOT / "start_spiral_os.py"
loader = SourceFileLoader("start_spiral_os", str(start_path))
spec = importlib.util.spec_from_loader("start_spiral_os", loader)
start_spiral_os = importlib.util.module_from_spec(spec)
loader.exec_module(start_spiral_os)


def _run_main(args):
    argv_backup = sys.argv.copy()
    sys.argv = ["start_spiral_os.py"] + args
    try:
        start_spiral_os.main()
    finally:
        sys.argv = argv_backup


def test_ritual_invocation_updates_state(mock_emotion_state, tmp_path, monkeypatch):
    purpose = tmp_path / "purpose.txt"
    analysis = tmp_path / "analysis.txt"
    suggestions = tmp_path / "suggestions.txt"
    invoke_path = tmp_path / "invoke.log"

    monkeypatch.setattr(start_spiral_os.glm_init, "PURPOSE_FILE", purpose)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "ANALYSIS_FILE", analysis)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "SUGGESTIONS_LOG", suggestions)

    monkeypatch.setattr(start_spiral_os.inanna_ai, "display_welcome_message", lambda: None)

    monkeypatch.setattr(start_spiral_os.logging.config, "dictConfig", lambda c: None)
    def fake_summary():
        purpose.write_text("ritual summary", encoding="utf-8")
        return "summary"

    def fake_analysis():
        analysis.write_text("ritual analysis", encoding="utf-8")
        return "analysis"

    def fake_suggest():
        suggestions.write_text("mystic insight", encoding="utf-8")
        return ["mystic insight"]

    monkeypatch.setattr(start_spiral_os.glm_init, "summarize_purpose", fake_summary)
    monkeypatch.setattr(start_spiral_os.glm_analyze, "analyze_code", fake_analysis)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "suggest_enhancement", fake_suggest)
    monkeypatch.setattr(start_spiral_os.inanna_ai, "reflect_existence", lambda: "id")
    monkeypatch.setattr(start_spiral_os.dnu, "monitor_traffic", lambda i, packet_count=5: None)

    monkeypatch.setattr(start_spiral_os.reflection_loop, "load_thresholds", lambda: {"default": 0.42})
    captured = {}
    def fake_adjust(detected, intended, tol):
        captured["args"] = (detected, intended, tol)

    monkeypatch.setattr(start_spiral_os.self_correction_engine, "adjust", fake_adjust)

    class DummyOrch:
        def handle_input(self, text):
            invoke_path.write_text(f"invoked {text}", encoding="utf-8")
            return {"text": "ok"}

    monkeypatch.setattr(start_spiral_os, "MoGEOrchestrator", lambda *a, **k: DummyOrch())
    monkeypatch.setattr(builtins, "input", lambda _="": "")

    _run_main(["--command", "❣⟁", "--skip-network", "--no-server", "--no-reflection"])

    assert purpose.read_text(encoding="utf-8") == "ritual summary"
    assert analysis.read_text(encoding="utf-8") == "ritual analysis"
    assert suggestions.read_text(encoding="utf-8") == "mystic insight"
    assert invoke_path.read_text(encoding="utf-8") == "invoked ❣⟁"

    assert captured["args"] == ("longing", "longing", 0.42)

    data = json.loads(mock_emotion_state.read_text())
    assert "last_emotion" in data
    assert data["last_emotion"] is not None
