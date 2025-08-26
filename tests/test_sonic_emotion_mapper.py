"""Tests for sonic emotion mapper."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import sonic_emotion_mapper as sem


def test_map_emotion_to_sound_rubedo():
    data = sem.map_emotion_to_sound("joy", "Rubedo")
    assert data["tempo"] == 140
    assert data["scale"] == "A_major"
    assert "trumpet" in data["timbre"]
    assert data["harmonics"] == "bright_major"
    assert set(data["qnl"]) == {"melody", "rhythm", "harmonics", "ambient"}


def test_map_emotion_to_sound_defaults():
    data = sem.map_emotion_to_sound("unknown", "Albedo")
    assert data["tempo"] == 100
    assert data["scale"] == "F_major"
    assert data["timbre"] == ["flute", "violin"]
    assert data["harmonics"] == "balanced_chords"


def test_load_mapping_cached(tmp_path, monkeypatch):
    """Ensure YAML mappings are cached."""

    path = tmp_path / "map.yaml"
    path.write_text("joy: {}")

    calls = {"count": 0}

    def fake_safe_load(f):
        calls["count"] += 1
        return {}

    monkeypatch.setattr(sem.yaml, "safe_load", lambda f: fake_safe_load(f))
    sem._load_mapping.cache_clear()

    sem._load_mapping(path)
    sem._load_mapping(path)

    assert calls["count"] == 1
