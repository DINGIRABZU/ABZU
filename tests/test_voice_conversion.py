import sys
from pathlib import Path
import types

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
np_mod = types.ModuleType("numpy")
np_mod.ndarray = object
sys.modules.setdefault("numpy", np_mod)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
req_mod = types.ModuleType("requests")
req_mod.post = lambda *a, **k: types.SimpleNamespace(json=lambda: {}, raise_for_status=lambda: None)
req_mod.get = req_mod.post
sys.modules.setdefault("requests", req_mod)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import voice_conversion
from INANNA_AI import speaking_engine


def test_apply_rvc_invokes_binary(monkeypatch, tmp_path):
    out_dir = tmp_path / "rvc"
    monkeypatch.setattr(voice_conversion.tempfile, "mkdtemp", lambda prefix="rvc_": str(out_dir))
    called = {}

    def fake_run(cmd, check):
        called["cmd"] = cmd
    monkeypatch.setattr(voice_conversion.subprocess, "run", fake_run)

    inp = tmp_path / "a.wav"
    inp.write_text("x")
    out = voice_conversion.apply_rvc(inp, "preset1")

    assert out == out_dir / "a.wav"
    assert called["cmd"] == [
        "rvc",
        "--preset",
        "preset1",
        "--input",
        str(inp),
        "--output",
        str(out),
    ]


def test_voicefix_invokes_binary(monkeypatch, tmp_path):
    called = {}
    def fake_run(cmd, check):
        called["cmd"] = cmd
    monkeypatch.setattr(voice_conversion.subprocess, "run", fake_run)

    inp = tmp_path / "b.wav"
    inp.write_text("x")
    out = voice_conversion.voicefix(inp)

    assert out == tmp_path / "b_vf.wav"
    assert called["cmd"] == ["voicefixer", "-i", str(inp), "-o", str(out)]


def test_synthesize_applies_converters(monkeypatch, tmp_path):
    engine = speaking_engine.SpeakingEngine()
    monkeypatch.setenv("RVC_PRESET", "demo")
    monkeypatch.setenv("VOICEFIX", "1")

    wav = tmp_path / "orig.wav"
    monkeypatch.setattr(speaking_engine, "synthesize_speech", lambda *a, **k: str(wav))

    calls = {}
    def fake_rvc(path: Path, preset: str) -> Path:
        calls["rvc"] = (path, preset)
        return tmp_path / "rvc.wav"
    def fake_vf(path: Path) -> Path:
        calls["vf"] = path
        return tmp_path / "final.wav"
    monkeypatch.setattr(voice_conversion, "apply_rvc", fake_rvc)
    monkeypatch.setattr(voice_conversion, "voicefix", fake_vf)

    out = engine.synthesize("hi", "calm")
    assert calls["rvc"] == (wav, "demo")
    assert calls["vf"] == tmp_path / "rvc.wav"
    assert out == str(tmp_path / "final.wav")
