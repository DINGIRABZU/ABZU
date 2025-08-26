"""Tests for enlightened prompt builder."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing the module under test
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
setattr(qlm_mod, "quantum_embed", lambda t: np.array([0.0]))
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)
sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))

from INANNA_AI.personality_layers.albedo.alchemical_persona import AlchemicalPersona, State
from INANNA_AI.personality_layers.albedo.enlightened_prompt import _build_enlightened_prompt


def test_deity_prompt_selection() -> None:
    persona = AlchemicalPersona()
    persona.state = State.NIGREDO
    out = _build_enlightened_prompt(persona, "the god speaks")
    assert out == "DEITY-nigredo-desc_nigredo:the god speaks"


def test_person_prompt_selection() -> None:
    persona = AlchemicalPersona()
    persona.state = State.ALBEDO
    out = _build_enlightened_prompt(persona, "Alice smiles")
    assert out == "PERSON-albedo-desc_albedo:Alice smiles"


def test_object_prompt_selection() -> None:
    persona = AlchemicalPersona()
    persona.state = State.CITRINITAS
    out = _build_enlightened_prompt(persona, "a stone rests")
    assert out == "OBJECT-citrinitas-desc_citrinitas:a stone rests"
