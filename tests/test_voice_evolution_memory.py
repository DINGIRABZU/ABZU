import sys
import types
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# stub optional dependencies
sys.modules.setdefault("yaml", types.ModuleType("yaml")).safe_load = lambda s: {}
dummy_np = types.ModuleType("numpy")
dummy_np.mean = lambda arr: sum(arr) / len(arr)
dummy_np.ndarray = object
sys.modules.setdefault("numpy", dummy_np)

from INANNA_AI import voice_evolution
import corpus_memory_logging
import emotional_state


def test_evolve_with_memory_updates_styles(tmp_path, monkeypatch, mock_emotion_state):
    log_file = tmp_path / "log.jsonl"
    monkeypatch.setattr(corpus_memory_logging, "INTERACTIONS_FILE", log_file)

    history = [
        {"emotion": "joy", "arousal": 0.6, "valence": 0.7, "sentiment": 0.2},
        {"emotion": "joy", "arousal": 0.7, "valence": 0.8, "sentiment": 0.4},
    ]
    with log_file.open("w", encoding="utf-8") as fh:
        for entry in history:
            fh.write(json.dumps(entry) + "\n")

    emotional_state.set_last_emotion("joy")

    evol = voice_evolution.VoiceEvolution()
    monkeypatch.setattr(voice_evolution, "_evolver", evol)

    evol.evolve_with_memory()

    arousal = sum(e["arousal"] for e in history) / len(history)
    valence = sum(e["valence"] for e in history) / len(history)
    sentiment = sum(e["sentiment"] for e in history) / len(history)
    new_speed = round(1.0 + (arousal - 0.5) * 0.4, 3)
    new_pitch = round((valence - 0.5) * 2.0, 3)
    weight = 1.0 + sentiment
    exp_speed = round((1.0 + new_speed * weight) / (1.0 + weight), 3)
    exp_pitch = round((0.0 + new_pitch * weight) / (1.0 + weight), 3)

    assert evol.styles["joy"]["speed"] == exp_speed
    assert evol.styles["joy"]["pitch"] == exp_pitch


def test_evolve_with_vector_memory(monkeypatch, mock_emotion_state):
    history = [
        {"emotion": "joy", "arousal": 0.6, "valence": 0.7, "sentiment": 0.2},
        {"emotion": "joy", "arousal": 0.7, "valence": 0.8, "sentiment": 0.4},
    ]

    dummy_vm = types.ModuleType("vector_memory")
    dummy_vm.query_vectors = lambda filter=None, limit=10: history
    added = {}

    def fake_add(text: str, meta: dict) -> None:
        added.update(meta)

    dummy_vm.add_vector = fake_add

    monkeypatch.setattr(voice_evolution, "vector_memory", dummy_vm)
    monkeypatch.setattr(
        voice_evolution.emotional_synaptic_engine,
        "adjust_from_memory",
        lambda: {
            "speed": voice_evolution._evolver.styles.get("joy", {}).get("speed", 1.0),
            "pitch": voice_evolution._evolver.styles.get("joy", {}).get("pitch", 0.0),
        },
    )

    evol = voice_evolution.VoiceEvolution()
    monkeypatch.setattr(voice_evolution, "_evolver", evol)
    emotional_state.set_last_emotion("joy")

    evol.evolve_with_memory()

    arousal = sum(e["arousal"] for e in history) / len(history)
    valence = sum(e["valence"] for e in history) / len(history)
    sentiment = sum(e["sentiment"] for e in history) / len(history)
    new_speed = round(1.0 + (arousal - 0.5) * 0.4, 3)
    new_pitch = round((valence - 0.5) * 2.0, 3)
    weight = 1.0 + sentiment
    exp_speed = round((1.0 + new_speed * weight) / (1.0 + weight), 3)
    exp_pitch = round((0.0 + new_pitch * weight) / (1.0 + weight), 3)

    assert evol.styles["joy"]["speed"] == exp_speed
    assert evol.styles["joy"]["pitch"] == exp_pitch
    assert added["emotion"] == "joy"
    assert added["speed"] == exp_speed
    assert added["pitch"] == exp_pitch

