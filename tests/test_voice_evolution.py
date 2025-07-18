import sys
from pathlib import Path
import types

qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
qlm_mod.quantum_embed = lambda t: [0.0]
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)

dummy_np = types.ModuleType("numpy")
dummy_np.mean = lambda arr: sum(arr) / len(arr)
dummy_np.clip = lambda x, low, high: low if x < low else high if x > high else x
dummy_np.array = lambda x, dtype=None: list(x)
sys.modules.setdefault("numpy", dummy_np)
import numpy as np
sys.modules.setdefault("yaml", types.ModuleType("yaml")).safe_load = lambda s: {}

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import voice_evolution

voice_evolution.vector_memory.query_vectors = lambda *a, **k: []


def test_update_from_history_modifies_style(monkeypatch):
    evol = voice_evolution.VoiceEvolution({'joy': {'speed': 1.0, 'pitch': 0.0}})
    monkeypatch.setattr(voice_evolution.db_storage, "save_voice_profiles", lambda *a, **k: None)
    history = [
        {'emotion': 'joy', 'arousal': 0.7, 'valence': 0.8, 'sentiment': 0.2},
        {'emotion': 'joy', 'arousal': 0.8, 'valence': 0.6, 'sentiment': 0.4},
    ]
    evol.update_from_history(history)
    arousal = float(np.mean([0.7, 0.8]))
    valence = float(np.mean([0.8, 0.6]))
    sentiment = float(np.mean([0.2, 0.4]))
    new_speed = round(1.0 + (arousal - 0.5) * 0.4, 3)
    new_pitch = round((valence - 0.5) * 2.0, 3)
    weight = 1.0 + sentiment
    exp_speed = round((1.0 + new_speed * weight) / (1.0 + weight), 3)
    exp_pitch = round((0.0 + new_pitch * weight) / (1.0 + weight), 3)
    assert evol.styles['joy']['speed'] == exp_speed
    assert evol.styles['joy']['pitch'] == exp_pitch


def test_get_params_returns_default_for_unknown():
    evol = voice_evolution.VoiceEvolution()
    params = evol.get_params('unknown')
    assert params['speed'] == evol.styles['neutral']['speed']
    assert params['pitch'] == evol.styles['neutral']['pitch']
    assert 'timbre' in params


def test_get_voice_params_uses_music_map(monkeypatch):
    monkeypatch.setattr(voice_evolution, "EMOTION_MUSIC_MAP", {"joy": {"scale": "D_minor"}})
    params = voice_evolution.get_voice_params("joy")
    assert params["key"] == "D_minor"
    assert params["pitch"] == voice_evolution.DEFAULT_VOICE_STYLES["neutral"]["pitch"] + voice_evolution.SCALE_PITCH["D_minor"]
