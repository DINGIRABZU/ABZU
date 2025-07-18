import sys
import types
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional modules
for name in [
    "opensmile",
    "EmotiVoice",
    "gtts",
    "openvoice",
    "sounddevice",
    "librosa",
    "soundfile",
    "stable_baselines3",
    "gymnasium",
]:
    sys.modules.setdefault(name, types.ModuleType(name))

sys.modules["soundfile"].write = lambda *a, **k: None

yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {"version": 1, "handlers": {}, "root": {"level": "INFO"}}
sys.modules.setdefault("yaml", yaml_mod)

class DummyPPO:
    def __init__(self, *a, **k):
        pass

sys.modules["stable_baselines3"].PPO = DummyPPO
gym_mod = sys.modules["gymnasium"]
gym_mod.Env = object
spaces_mod = types.ModuleType("spaces")

class DummyBox:
    def __init__(self, *a, **k):
        pass

spaces_mod.Box = DummyBox
gym_mod.spaces = spaces_mod

from INANNA_AI_AGENT import INANNA_AI
from INANNA_AI import speaking_engine
from tools import voice_conversion
from core import avatar_expression_engine, expressive_output
import vector_memory


def test_voice_avatar_pipeline(tmp_path, monkeypatch):
    wav = tmp_path / "song.wav"
    json_out = tmp_path / "meta.json"

    # Fake QNL generation
    def fake_run_qnl(hex_input, wav=wav, json_file=json_out):
        Path(wav).write_bytes(b"00")
        Path(json_file).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(inanna_ai, "run_qnl", fake_run_qnl)

    argv = sys.argv
    sys.argv = ["INANNA_AI.py", "--hex", "00ff", "--wav", str(wav), "--json", str(json_out)]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv

    # Mock speech synthesis
    speech = tmp_path / "speech.wav"
    def fake_synth(text, emotion, history=None, timbre="neutral"):
        speech.write_bytes(b"01")
        return str(speech)
    monkeypatch.setattr(speaking_engine, "synthesize_speech", fake_synth)

    calls = {}
    def fake_rvc(path: Path, preset: str) -> Path:
        calls["rvc"] = (path, preset)
        return tmp_path / "rvc.wav"
    def fake_vf(path: Path) -> Path:
        calls["vf"] = path
        return tmp_path / "final.wav"
    monkeypatch.setattr(voice_conversion, "apply_rvc", fake_rvc)
    monkeypatch.setattr(voice_conversion, "voicefix", fake_vf)
    monkeypatch.setenv("RVC_PRESET", "demo")
    monkeypatch.setenv("VOICEFIX", "1")

    engine = speaking_engine.SpeakingEngine()
    out_path = Path(engine.synthesize("hello", "joy"))
    assert calls["rvc"] == (speech, "demo")
    assert calls["vf"] == tmp_path / "rvc.wav"

    frames = []
    def fake_stream(path: Path, fps: int = 15):
        frames.append(path)
        yield np.zeros((1, 1, 3), dtype=np.uint8)
    monkeypatch.setattr(avatar_expression_engine, "stream_avatar_audio", fake_stream)

    expressive_output._handle_audio(str(out_path))
    assert frames and frames[0] == out_path

    if vector_memory.LOG_FILE.exists():
        vector_memory.LOG_FILE.unlink()
    monkeypatch.setattr(vector_memory.qnl_utils, "quantum_embed", lambda t: np.zeros(1))
    class DummyCollection:
        def add(self, ids, embeddings, metadatas):
            pass
    monkeypatch.setattr(vector_memory, "_get_collection", lambda: DummyCollection())
    vector_memory.add_vector("test", {"src": str(out_path)})

    logs = vector_memory.LOG_FILE.read_text(encoding="utf-8").splitlines()
    assert logs and '"operation": "add"' in logs[-1]
