import sys
from pathlib import Path
import types
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import voice_aura


def test_sox_effect_chain(monkeypatch, tmp_path):
    inp = tmp_path / "in.wav"
    inp.write_text("x")
    out = tmp_path / "out.wav"

    class DummyTmp:
        def __init__(self, name):
            self.name = str(name)
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(voice_aura.tempfile, "NamedTemporaryFile", lambda **k: DummyTmp(out))
    monkeypatch.setattr(voice_aura, "sox_available", lambda: True)
    monkeypatch.setattr(voice_aura.emotional_state, "get_last_emotion", lambda: "joy")

    called = {}
    def fake_run(cmd, check):
        called["cmd"] = cmd
    monkeypatch.setattr(voice_aura.subprocess, "run", fake_run)

    result = voice_aura.apply_voice_aura(inp)

    assert result == out
    assert called["cmd"] == [
        "sox",
        str(inp),
        str(out),
        "reverb",
        "30",
        "delay",
        "0.080",
    ]


def test_rave_timbre_blend(monkeypatch, tmp_path):
    inp = tmp_path / "in.wav"
    inp.write_text("x")
    out = tmp_path / "out.wav"

    class DummyTmp:
        def __init__(self, name):
            self.name = str(name)
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass

    # force pydub path
    monkeypatch.setattr(voice_aura, "sox_available", lambda: False)

    class DummySeg:
        def export(self, path, format="wav"):
            calls["export"] = path
    def fake_from_file(path):
        calls["loaded"] = path
        return DummySeg()

    calls = {}
    monkeypatch.setattr(voice_aura, "AudioSegment", types.SimpleNamespace(from_file=fake_from_file))
    monkeypatch.setattr(voice_aura, "_apply_pydub_effects", lambda seg, r, d: seg)
    monkeypatch.setattr(voice_aura.tempfile, "NamedTemporaryFile", lambda **k: DummyTmp(out))
    monkeypatch.setattr(voice_aura.emotional_state, "get_last_emotion", lambda: "sad")

    monkeypatch.setattr(voice_aura.sf, "read", lambda p, dtype="float32": (np.zeros(2, dtype=np.float32), 44100))
    def fake_morph(a, b, sr, amount, checkpoint):
        calls["morph"] = checkpoint
        return np.ones_like(a), sr
    monkeypatch.setattr(voice_aura, "rave_morph", fake_morph)
    monkeypatch.setattr(voice_aura.sf, "write", lambda p, d, sr: calls.setdefault("write", p))

    result = voice_aura.apply_voice_aura(inp, rave_checkpoint=Path("model.pt"), amount=0.3)

    assert calls["loaded"] == inp
    assert calls["export"] == out
    assert calls["morph"] == Path("model.pt")
    assert calls["write"] == out
    assert result == out
