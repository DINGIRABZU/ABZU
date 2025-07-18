from __future__ import annotations

"""Lightweight emotion analysis tools using Librosa."""

from typing import Dict, Any, Tuple

# Mapping from emotional labels to Jungian archetypes
EMOTION_ARCHETYPES = {
    "joy": "Jester",
    "stress": "Warrior",
    "fear": "Orphan",
    "sad": "Caregiver",
    "excited": "Hero",
    "calm": "Sage",
    "citrinitas_layer": "Citrinitas",
    "neutral": "Everyman",
}

# Coarse weight for each emotion; can be used by higher level modules
EMOTION_WEIGHT = {
    "joy": 1.0,
    "stress": 0.8,
    "fear": 0.8,
    "sad": 0.7,
    "excited": 0.6,
    "calm": 0.4,
    "neutral": 0.2,
}

# Simple mapping from emotion to a descriptive "quantum tone"
EMOTION_QUANTUM_TONE = {
    "joy": "Radiant",
    "stress": "Tension",
    "fear": "Flicker",
    "sad": "Echo",
    "excited": "Burst",
    "calm": "Drift",
    "neutral": "Still",
}

_CURRENT_STATE = {
    "emotion": "neutral",
    "archetype": EMOTION_ARCHETYPES["neutral"],
    "weight": EMOTION_WEIGHT["neutral"],
}

import librosa
import numpy as np
import opensmile



def analyze_audio_emotion(audio_path: str) -> Dict[str, Any]:
    """Return an emotion estimate for ``audio_path``.

    The analysis extracts pitch and tempo using ``librosa`` and uses
    ``openSMILE``'s eGeMAPSv02 configuration to obtain coarse arousal and
    valence scores. A basic rule-based classifier then derives a discrete
    emotion label from these values.
    """
    wave, sr = librosa.load(audio_path, sr=None, mono=True)

    f0 = librosa.yin(
        wave,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )
    pitch = float(np.nanmean(f0))

    tempo, _ = librosa.beat.beat_track(y=wave, sr=sr)
    tempo = float(np.atleast_1d(tempo)[0])

    smile = opensmile.Smile(
        feature_set=opensmile.FeatureSet.eGeMAPSv02,
        feature_level=opensmile.FeatureLevel.Functionals,
    )
    feats = smile.process_signal(wave, sr).iloc[0]
    loudness = float(feats["loudness_sma3_amean"])
    hnr = float(feats.get("HNRdBACF_sma3nz_amean", 0.0))

    arousal = max(0.0, min(1.0, (loudness + 60.0) / 60.0))
    valence = max(0.0, min(1.0, (hnr + 20.0) / 40.0))

    energy = float(np.mean(np.abs(wave)))

    emotion = "neutral"
    if arousal > 0.75:
        emotion = "stress"
    elif valence < 0.3 and arousal > 0.5:
        emotion = "fear"
    elif valence > 0.7 and arousal > 0.5:
        emotion = "joy"
    elif valence < 0.4 and arousal < 0.4:
        emotion = "sad"
    elif pitch > 180 and tempo > 120:
        emotion = "excited"
    elif pitch < 120 and tempo < 90:
        emotion = "calm"

    _CURRENT_STATE["emotion"] = emotion
    _CURRENT_STATE["archetype"] = EMOTION_ARCHETYPES.get(emotion, "Everyman")
    _CURRENT_STATE["weight"] = EMOTION_WEIGHT.get(emotion, 0.0)
    _CURRENT_STATE["arousal"] = arousal
    _CURRENT_STATE["valence"] = valence

    return {
        "emotion": emotion,
        "pitch": round(pitch, 2),
        "tempo": round(tempo, 2),
        "arousal": round(arousal, 3),
        "valence": round(valence, 3),
    }

def get_current_archetype() -> str:
    """Return the Jungian archetype for the last analyzed emotion."""
    return _CURRENT_STATE["archetype"]


def get_emotional_weight() -> float:
    """Return a coarse numeric weight for the last analyzed emotion."""
    return _CURRENT_STATE["weight"]


def emotion_to_archetype(emotion: str) -> str:
    """Map an emotion label to its corresponding Jungian archetype."""
    return EMOTION_ARCHETYPES.get(emotion, "Everyman")


def emotion_weight(emotion: str) -> float:
    """Return the weight associated with ``emotion``."""
    return EMOTION_WEIGHT.get(emotion, 0.0)


def get_emotion_and_tone(emotion: str | None = None) -> Tuple[str, str]:
    """Return ``emotion`` and its associated quantum tone."""

    if emotion is None:
        emotion = _CURRENT_STATE["emotion"]
    tone = EMOTION_QUANTUM_TONE.get(emotion, "Still")
    return emotion, tone


__all__ = [
    "analyze_audio_emotion",
    "get_current_archetype",
    "get_emotional_weight",
    "emotion_to_archetype",
    "emotion_weight",
    "get_emotion_and_tone",
]
