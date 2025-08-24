"""Smoke tests for transformation engines."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import archetype_shift_engine as ase  # noqa: E402
import learning_mutator as lm  # noqa: E402
from state_transition_engine import StateTransitionEngine  # noqa: E402


def test_transformation_smoke(monkeypatch):
    matrix = {"bad": {"counts": {"total": 4, "success": 1}}}
    monkeypatch.setattr(
        lm, "load_intents", lambda path=None: {"bad": {"synonyms": ["awful"]}}
    )
    suggestions = lm.propose_mutations(matrix)
    assert suggestions

    ste = StateTransitionEngine()
    ste.update_state("begin the ritual now")
    assert ste.current_state() == "ritual"

    monkeypatch.setattr(ase.emotion_registry, "get_resonance_level", lambda: 0.9)
    monkeypatch.setattr(ase.emotion_registry, "get_current_layer", lambda: "albedo")
    layer = ase.maybe_shift_archetype("hello", "anger")
    assert layer == "nigredo_layer"
