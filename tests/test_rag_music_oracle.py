import sys
from pathlib import Path
import types

from tests.helpers import emotion_stub
from tests.helpers.config_stub import build_settings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy dependencies before importing the module
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
fake_pkg = types.ModuleType("INANNA_AI")
setattr(fake_pkg, "emotion_analysis", emotion_stub)
sys.modules.setdefault("INANNA_AI", fake_pkg)
sys.modules["INANNA_AI.emotion_analysis"] = emotion_stub

config_mod = types.ModuleType("config")
config_mod.settings = build_settings()
config_mod.reload = lambda: None
sys.modules.setdefault("config", config_mod)

# Minimal play_ritual_music stub
fake_play = types.ModuleType("play_ritual_music")
fake_play.compose_ritual_music = lambda *a, **k: Path("out.wav")
sys.modules.setdefault("play_ritual_music", fake_play)

import rag_music_oracle as rmo


def test_answer_with_audio(tmp_path, monkeypatch):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"\x00\x00")

    monkeypatch.setattr(rmo.emotion_analysis, "analyze_audio_emotion", lambda p: {
        "emotion": "sad",
        "tempo": 80.0,
        "pitch": 120.0,
        "arousal": 0.3,
        "valence": 0.2,
    })
    monkeypatch.setattr(rmo.rag_engine, "query", lambda q, top_n=5: [{"snippet": "melancholic motif"}])
    monkeypatch.setattr(rmo.play_ritual_music, "compose_ritual_music", lambda e, r, **k: tmp_path / "out.wav")

    text, out = rmo.answer("How does this MP3 express grief?", audio, play=True)
    assert "sad" in text
    assert "melancholic motif" in text
    assert out == tmp_path / "out.wav"


def test_cli_output(tmp_path, monkeypatch, capsys):
    audio = tmp_path / "song.wav"
    audio.write_bytes(b"\x00\x00")

    monkeypatch.setattr(rmo, "answer", lambda q, a=None, play=False, ritual="\u2609": ("txt", None))

    rmo.main(["question", "--audio", str(audio)])
    out = capsys.readouterr().out
    assert "txt" in out

