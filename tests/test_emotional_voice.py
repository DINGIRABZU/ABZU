import sys
import json
import types
from pathlib import Path

qlm_mod = types.ModuleType("MUSIC_FOUNDATION.qnl_utils")
qlm_mod.quantum_embed = lambda t: [0.0]
sys.modules.setdefault("MUSIC_FOUNDATION.qnl_utils", qlm_mod)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# stub heavy optional libraries
class DummyTTS:
    def __init__(self, text):
        self.text = text
    def save(self, path):
        Path(path).write_bytes(b"dummy")

dummy_gtts = types.ModuleType("gtts")
dummy_gtts.gTTS = DummyTTS
sys.modules.setdefault("gtts", dummy_gtts)
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("sounddevice", types.ModuleType("sounddevice"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("yaml", types.ModuleType("yaml")).safe_load = lambda s: {}

dummy_np = types.ModuleType("numpy")
dummy_np.mean = lambda arr: sum(arr) / len(arr)
dummy_np.clip = lambda x, low, high: low if x < low else high if x > high else x
dummy_np.array = lambda x, dtype=None: list(x)
sys.modules.setdefault("numpy", dummy_np)

from INANNA_AI import emotional_synaptic_engine, voice_evolution, speaking_engine

voice_evolution.vector_memory.query_vectors = lambda *a, **k: []
import corpus_memory_logging
import emotional_state


HISTORY = [
    {"emotion": "joy", "arousal": 0.7, "valence": 0.8, "sentiment": 0.3},
    {"emotion": "calm", "arousal": 0.4, "valence": 0.4, "sentiment": 0.1},
]


def _expected_filters(history):
    tmp = voice_evolution.VoiceEvolution()
    tmp.update_from_history(history)
    style = tmp.styles[history[-1]["emotion"]]
    return emotional_synaptic_engine.map_emotion_to_filters(history[-1]["emotion"], style=style)


def test_adjust_from_memory_returns_expected_filters(monkeypatch):
    evol = voice_evolution.VoiceEvolution()
    monkeypatch.setattr(voice_evolution, "_evolver", evol)
    monkeypatch.setattr(voice_evolution.db_storage, "save_voice_profiles", lambda *a, **k: None)

    filters = emotional_synaptic_engine.adjust_from_memory(HISTORY)
    expected = _expected_filters(HISTORY)

    assert filters == expected
    assert evol.styles["calm"]["speed"] == expected["speed"]
    assert evol.styles["calm"]["pitch"] == expected["pitch"]


def test_evolve_with_memory_updates_internal_styles(monkeypatch, tmp_path, mock_emotion_state):
    log_file = tmp_path / "interactions.jsonl"
    monkeypatch.setattr(corpus_memory_logging, "INTERACTIONS_FILE", log_file)
    with log_file.open("w", encoding="utf-8") as fh:
        for entry in HISTORY:
            fh.write(json.dumps(entry) + "\n")

    evol = voice_evolution.VoiceEvolution()
    monkeypatch.setattr(voice_evolution, "_evolver", evol)
    monkeypatch.setattr(voice_evolution.db_storage, "save_voice_profiles", lambda *a, **k: None)
    emotional_state.set_last_emotion("calm")

    evol.evolve_with_memory()

    expected = _expected_filters(HISTORY)
    assert evol.styles["calm"]["speed"] == expected["speed"]
    assert evol.styles["calm"]["pitch"] == expected["pitch"]


def test_speak_triggers_reflector(monkeypatch):
    events = {}
    engine = speaking_engine.SpeakingEngine()
    monkeypatch.setattr(engine, "synthesize", lambda *a, **k: "out.wav")
    monkeypatch.setattr(engine, "play", lambda p: events.setdefault("play", p))
    monkeypatch.setattr(voice_evolution.db_storage, "save_voice_profiles", lambda *a, **k: None)

    dummy_reflector = types.SimpleNamespace(reflect=lambda p: events.setdefault("reflect", p))
    monkeypatch.setitem(sys.modules, "INANNA_AI.speech_loopback_reflector", dummy_reflector)

    result = engine.speak("hi", "joy", reflect=True)

    assert result == "out.wav"
    assert events.get("play") == "out.wav"
    assert events.get("reflect") == "out.wav"
