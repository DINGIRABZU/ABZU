import sys
from pathlib import Path
import types

sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("yaml", types.ModuleType("yaml")).safe_load = lambda s: {}

dummy_np = types.ModuleType("numpy")
dummy_np.mean = lambda arr: sum(arr) / len(arr)
dummy_np.clip = lambda x, low, high: low if x < low else high if x > high else x
dummy_np.array = lambda x, dtype=None: list(x)
sys.modules.setdefault("numpy", dummy_np)

qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
qlm_mod.quantum_embed = lambda t: [0.0]
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import db_storage, voice_evolution, utils

voice_evolution.vector_memory.query_vectors = lambda *a, **k: []


def test_voice_profile_storage(tmp_path):
    db = tmp_path / "voice.db"
    db_storage.init_db(db)
    profile = {"joy": {"speed": 1.2, "pitch": 0.3}}
    db_storage.save_voice_profiles(profile, db_path=db)
    out = db_storage.fetch_voice_profiles(db_path=db)
    assert out == profile


def test_update_with_sentiment(monkeypatch):
    evol = voice_evolution.VoiceEvolution({"joy": {"speed": 1.0, "pitch": 0.0}})
    monkeypatch.setattr(voice_evolution.db_storage, "save_voice_profiles", lambda *a, **k: None)
    score = utils.sentiment_score("I love this good day")
    history = [{"emotion": "joy", "arousal": 0.6, "valence": 0.8, "sentiment": score}]
    evol.update_from_history(history)
    new_speed = round(1.0 + (0.6 - 0.5) * 0.4, 3)
    new_pitch = round((0.8 - 0.5) * 2.0, 3)
    weight = 1.0 + score
    expected_speed = round((1.0 + new_speed * weight) / (1.0 + weight), 3)
    expected_pitch = round((0.0 + new_pitch * weight) / (1.0 + weight), 3)
    assert evol.styles["joy"]["speed"] == expected_speed
    assert evol.styles["joy"]["pitch"] == expected_pitch


def test_store_and_load_profiles(tmp_path):
    db = tmp_path / "v.db"
    db_storage.init_db(db)
    evol = voice_evolution.VoiceEvolution()
    evol.styles["calm"]["speed"] = 0.8
    evol.store_profiles(db)
    other = voice_evolution.VoiceEvolution()
    other.load_profiles(db)
    assert other.styles["calm"]["speed"] == 0.8

