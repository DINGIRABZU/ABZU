"""Heuristics for selecting a language model in the Crown agent."""
from __future__ import annotations

from typing import Any, Dict
from statistics import mean
import os
import time

from task_profiling import classify_task
import servant_model_manager as smm
from INANNA_AI import emotional_memory
import emotional_state
import vector_memory
import voice_aura

_ROTATION_PERIOD = int(os.getenv("LLM_ROTATION_PERIOD", "300"))
_MAX_FAILURES = int(os.getenv("LLM_MAX_FAILURES", "3"))

_FAIL_COUNTS: dict[str, int] = {}
_DISABLED_UNTIL: dict[str, float] = {}
_WINDOW_START: dict[str, float] = {}

_INSTRUCTION_TRIGGERS = {"how", "explain", "tutorial"}
_PHILOSOPHY_TRIGGERS = {"why", "meaning", "purpose"}


def _enabled(name: str) -> bool:
    """Return ``True`` if ``name`` is not temporarily disabled."""
    return _DISABLED_UNTIL.get(name, 0) <= time.time()


def record_result(name: str, success: bool) -> None:
    """Record ``success`` for ``name`` and disable if needed."""
    now = time.time()
    start = _WINDOW_START.get(name)
    if start is None:
        _WINDOW_START[name] = now
    elif now - start >= _ROTATION_PERIOD:
        _DISABLED_UNTIL[name] = now + _ROTATION_PERIOD
        _FAIL_COUNTS[name] = 0
        _WINDOW_START[name] = now

    if success:
        _FAIL_COUNTS[name] = 0
        return

    count = _FAIL_COUNTS.get(name, 0) + 1
    _FAIL_COUNTS[name] = count
    if count >= _MAX_FAILURES:
        _DISABLED_UNTIL[name] = now + _ROTATION_PERIOD
        _FAIL_COUNTS[name] = 0
        _WINDOW_START[name] = now


def recommend_llm(task_type: str, emotion: str) -> str:
    """Return the best LLM name for ``task_type`` and ``emotion``."""
    best = "glm"
    best_score = -1.0

    for name in smm.list_models():
        if not _enabled(name):
            continue
        history = emotional_memory.query_history(name)
        relevant = [
            node
            for node in history
            if classify_task(node.prompt) == task_type
        ]
        if len(relevant) < 3:
            continue

        successes = sum(1 for n in relevant if n.success)
        success_rate = successes / len(relevant)
        resonance = 0.0
        for n in relevant:
            aff = emotional_memory.score_affect(n.response, n.emotion)
            resonance += aff["joy"] + aff["trust"] - aff["friction"]
        resonance /= len(relevant)

        score = success_rate + resonance
        if score > best_score:
            best_score = score
            best = name

    return best


def decide_expression_options(emotion: str) -> Dict[str, Any]:
    """Return TTS backend, avatar style and aura amount."""
    soul = (emotional_state.get_soul_state() or "").lower()
    try:
        history = vector_memory.query_vectors(filter={"type": "emotion"}, limit=10)
    except Exception:
        history = []

    valences = [float(h.get("valence", 0.5)) for h in history if h.get("valence") is not None]
    arousals = [float(h.get("arousal", 0.5)) for h in history if h.get("arousal") is not None]
    avg_valence = mean(valences) if valences else 0.5
    avg_arousal = mean(arousals) if arousals else 0.5

    if soul == "awakened":
        backend = "coqui"
    elif avg_arousal > 0.7:
        backend = "bark"
    else:
        backend = "gtts"

    if avg_valence > 0.6:
        avatar = "Soprano"
    elif avg_valence < 0.4:
        avatar = "Baritone"
    else:
        avatar = "Androgynous"

    aura_amount = max(0.0, min(1.0, 0.5 + (avg_arousal - 0.5)))
    aura = voice_aura.EFFECT_PRESETS.get(emotion.lower(), voice_aura.EFFECT_PRESETS["neutral"])

    return {
        "tts_backend": backend,
        "avatar_style": avatar,
        "aura_amount": round(aura_amount, 3),
        "aura": aura,
        "soul_state": soul,
    }


__all__ = ["recommend_llm", "record_result", "decide_expression_options"]
