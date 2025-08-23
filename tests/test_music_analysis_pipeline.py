"""Tests for music analysis pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline import music_analysis


def test_analyze_music(monkeypatch):
    dummy_wave = np.zeros(100)
    monkeypatch.setattr(music_analysis, "load_audio", lambda p: (dummy_wave, 44100))
    monkeypatch.setattr(
        music_analysis,
        "extract_mfcc",
        lambda s, sr: np.ones((2, 3)),
    )
    monkeypatch.setattr(music_analysis, "extract_key", lambda s: "C:maj")
    monkeypatch.setattr(music_analysis, "extract_tempo", lambda s, sr: 120.0)
    monkeypatch.setattr(
        music_analysis,
        "analyze_audio_emotion",
        lambda p: {"emotion": "joy"},
    )

    result = music_analysis.analyze_music(Path("song.wav"))
    assert result.features == {"mfcc": [1.0, 1.0], "key": "C:maj", "tempo": 120.0}
    assert result.emotion == {"emotion": "joy"}
    assert result.metadata["sr"] == 44100


def test_cli_output(monkeypatch, capsys):
    dummy = music_analysis.MusicAnalysisResult(
        features={"tempo": 120},
        emotion={"emotion": "joy"},
        metadata={"path": "x.wav", "sr": 44100, "duration": 0.0},
    )
    monkeypatch.setattr(music_analysis, "analyze_music", lambda p: dummy)
    music_analysis.main(["x.wav"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["emotion"]["emotion"] == "joy"
