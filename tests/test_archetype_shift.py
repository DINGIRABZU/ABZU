from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_shift_engine as ase
import emotion_registry


def test_ritual_keyword_triggers_citrinitas(monkeypatch):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.5)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: None)
    layer = ase.maybe_shift_archetype("begin the ritual ☉", "joy")
    assert layer == "citrinitas_layer"


def test_emotional_overload_shift(monkeypatch):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.9)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: "albedo")
    layer = ase.maybe_shift_archetype("hello", "anger")
    assert layer == "nigredo_layer"


def test_failed_update_logs_exception(monkeypatch, caplog):
    monkeypatch.setattr(emotion_registry, "get_resonance_level", lambda: 0.9)
    monkeypatch.setattr(emotion_registry, "get_current_layer", lambda: None)

    def boom(layer: str) -> None:  # pragma: no cover - raising for test
        raise RuntimeError("boom")

    monkeypatch.setattr(ase.soul_state_manager, "update_archetype", boom)
    with caplog.at_level(logging.ERROR):
        layer = ase.maybe_shift_archetype("hello", "anger")
    assert layer == "nigredo_layer"
    assert any("Failed to update archetype" in r.message for r in caplog.records)
