import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.speaking_engine import SpeakingEngine


def test_speaking_engine_speak(monkeypatch):
    engine = SpeakingEngine()
    calls = []

    monkeypatch.setattr(engine, "synthesize", lambda text, emotion: "file.wav")
    monkeypatch.setattr(engine, "play", lambda path: calls.append(path))

    path = engine.speak("hi", "calm")

    assert path == "file.wav"
    assert calls == ["file.wav"]

