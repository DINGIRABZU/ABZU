"""Lightweight emotion analysis tools using Librosa."""

from __future__ import annotations

from typing import Any, Dict, Tuple

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

import numpy as np

try:  # pragma: no cover - optional dependency
    import librosa
except Exception:  # pragma: no cover - optional dependency
    librosa = None  # type: ignore

try:  # pragma: no cover - optional dependency
    import opensmile
except Exception:  # pragma: no cover - optional dependency
    opensmile = None  # type: ignore

# Optional ML-based classifier support
try:  # pragma: no cover - optional dependency
    import torch

    from transformers import AutoModelForAudioClassification, AutoProcessor
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore
    AutoModelForAudioClassification = AutoProcessor = None  # type: ignore


def predict_emotion_ml(
    audio_path: str, model_name: str = "m-a-p/MERT-v1-330M-CLAP"
) -> Dict[str, float]:
    """Return emotion probabilities from a pretrained model.

    Parameters
    ----------
    audio_path:
        Path to the audio file to analyze.
    model_name:
        Hugging Face model identifier. Defaults to a MERT/CLAP variant.

    Returns
    -------
    Dict[str, float]
        Mapping from emotion label to probability.

    Raises
    ------
    RuntimeError
        If required libraries are missing or the model cannot be loaded.
    """

    if (
        torch is None
        or AutoModelForAudioClassification is None
        or AutoProcessor is None
        or librosa is None
    ):
        raise RuntimeError("transformers, torch and librosa are required")

    wave, sr = librosa.load(audio_path, sr=16000, mono=True)
    processor = AutoProcessor.from_pretrained(model_name)
    model = AutoModelForAudioClassification.from_pretrained(model_name)
    inputs = processor(wave, sampling_rate=sr, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0]
    probs = torch.nn.functional.softmax(logits, dim=-1).cpu().numpy()
    labels = model.config.id2label
    return {labels[i]: float(probs[i]) for i in range(len(labels))}


def _rule_based_classify(
    pitch: float, tempo: float, arousal: float, valence: float
) -> str:
    """Return a discrete emotion using the heuristic rules."""

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
    return emotion


def analyze_audio_emotion(
    audio_path: str, use_ml: bool = False, model_name: str | None = None
) -> Dict[str, Any]:
    """Return an emotion estimate for ``audio_path``.

    The analysis extracts pitch and tempo using ``librosa`` and uses
    ``openSMILE``'s eGeMAPSv02 configuration to obtain coarse arousal and
    valence scores. A basic rule-based classifier derives a discrete emotion
    label from these values. If ``use_ml`` is ``True`` and a compatible
    pretrained model is available, the classifier result is replaced by the
    model prediction. When the model cannot be loaded the heuristic classifier
    is used as a fallback.
    """
    if librosa is None or opensmile is None:
        raise RuntimeError("librosa and opensmile libraries are required")
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

    emotion = _rule_based_classify(pitch, tempo, arousal, valence)

    probs: Dict[str, float] | None = None
    if use_ml:
        try:
            probs = predict_emotion_ml(
                audio_path, model_name or "m-a-p/MERT-v1-330M-CLAP"
            )
            if probs:
                emotion = max(probs, key=probs.get)
        except Exception:
            probs = None

    _CURRENT_STATE["emotion"] = emotion
    _CURRENT_STATE["archetype"] = EMOTION_ARCHETYPES.get(emotion, "Everyman")
    _CURRENT_STATE["weight"] = EMOTION_WEIGHT.get(emotion, 0.0)
    _CURRENT_STATE["arousal"] = arousal
    _CURRENT_STATE["valence"] = valence

    result: Dict[str, Any] = {
        "emotion": emotion,
        "pitch": round(pitch, 2),
        "tempo": round(tempo, 2),
        "arousal": round(arousal, 3),
        "valence": round(valence, 3),
    }
    if probs is not None:
        result["probabilities"] = {
            k: round(float(v), 3) for k, v in sorted(probs.items(), key=lambda x: -x[1])
        }
    return result


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
    "predict_emotion_ml",
    "get_current_archetype",
    "get_emotional_weight",
    "emotion_to_archetype",
    "emotion_weight",
    "get_emotion_and_tone",
]
