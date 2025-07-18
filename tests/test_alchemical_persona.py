from pathlib import Path
import sys
import types
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

from INANNA_AI.personality_layers.albedo import AlchemicalPersona, State


def test_trigger_detection_and_metrics():
    persona = AlchemicalPersona()
    entity, triggers = persona.detect_state_trigger("Alice feels love and joy")
    assert entity == "person"
    assert triggers == {"affection", "joy"}
    persona.update_metrics(triggers)
    assert persona.entanglement > 0
    assert persona.shadow_balance == 0.0


def test_weighted_state_transitions():
    seq = iter([0.1, 0.6])
    persona = AlchemicalPersona(weights={s: 0.5 for s in State}, rng=lambda: next(seq))
    assert persona.state is State.NIGREDO
    persona.advance()
    assert persona.state is State.ALBEDO  # 0.1 < 0.5 -> advance
    persona.advance()
    assert persona.state is State.ALBEDO  # 0.6 > 0.5 -> stay


def test_four_state_cycle():
    seq = iter([0.2, 0.2, 0.2, 0.2])
    persona = AlchemicalPersona(weights={s: 0.5 for s in State}, rng=lambda: next(seq))
    states = []
    for _ in range(4):
        persona.advance()
        states.append(persona.state)
    assert states == [
        State.ALBEDO,
        State.RUBEDO,
        State.CITRINITAS,
        State.NIGREDO,
    ]

