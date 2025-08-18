import sys
from pathlib import Path
import types

from tests.helpers import emotion_stub
from tests.helpers.config_stub import build_settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub external dependencies to allow importing inanna_ai.main
sf = types.ModuleType("soundfile")
sf.write = lambda *a, **k: None
sys.modules.setdefault("soundfile", sf)

np = types.ModuleType("numpy")
np.random = types.SimpleNamespace(rand=lambda *a, **k: 0)
np.int16 = "int16"
sys.modules.setdefault("numpy", np)
sys.modules.setdefault("torch", types.ModuleType("torch"))
sys.modules.setdefault("torch.nn", types.ModuleType("torch.nn"))
sys.modules["torch.nn"].Module = object

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules["librosa"].load = lambda *a, **k: ([], 0)
sys.modules.setdefault("qnl_engine", types.ModuleType("qnl_engine"))

sys.modules.setdefault("orchestrator", types.ModuleType("orchestrator"))
sys.modules["orchestrator"].MoGEOrchestrator = lambda: None

sys.modules.setdefault("INANNA_AI.response_manager", types.ModuleType("response_manager"))
sys.modules.setdefault("INANNA_AI.tts_coqui", types.ModuleType("tts_coqui"))
sys.modules["INANNA_AI.emotion_analysis"] = emotion_stub
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))

sys.modules.setdefault("INANNA_AI.gates", types.ModuleType("gates"))
sys.modules["INANNA_AI.gates"].sign_blob = lambda *a, **k: b""
sys.modules["INANNA_AI.gates"].verify_blob = lambda *a, **k: True

sys.modules["INANNA_AI.utils"] = types.ModuleType("utils")
sys.modules["INANNA_AI.utils"].setup_logger = lambda: None
sys.modules["INANNA_AI.utils"].sentiment_score = lambda text: 0.0
sys.modules["INANNA_AI.stt_whisper"] = types.ModuleType("stt_whisper")
sys.modules["INANNA_AI.stt_whisper"].transcribe_audio = lambda p: ""
sys.modules["INANNA_AI.listening_engine"] = types.ModuleType("listening_engine")
sys.modules["INANNA_AI.listening_engine"].ListeningEngine = lambda: None
sys.modules["INANNA_AI.speaking_engine"] = types.ModuleType("speaking_engine")
sys.modules["INANNA_AI.speaking_engine"].SpeakingEngine = lambda: None
sys.modules["INANNA_AI.db_storage"] = types.ModuleType("db_storage")
sys.modules["INANNA_AI.db_storage"].init_db = lambda: None
sys.modules["INANNA_AI.db_storage"].save_interaction = lambda *a, **k: None

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)

from INANNA_AI import main as voice_main


def test_soul_ritual_formats_phrase(monkeypatch):
    dummy_core = type(
        "C",
        (),
        {
            "execute": lambda self, vec: "grid",
            "grid": type("G", (), {"size": 1})(),
            "shape": (),
            "__init__": lambda self: None,
        },
    )()
    dummy_gate = type("G", (), {"process_outward": lambda self, g: "gate_text"})()
    monkeypatch.setattr(voice_main, "RFA7D", lambda: dummy_core)
    monkeypatch.setattr(voice_main, "GateOrchestrator", lambda: dummy_gate)

    out = []
    phrase = voice_main.soul_ritual({"emotion": "joy"}, out)
    assert phrase == "Ritual gate echo: gate_text [joy]"
    assert out == [phrase]
