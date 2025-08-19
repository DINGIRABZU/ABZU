from __future__ import annotations

"""Lightweight orchestrator for the Crown console."""

from typing import Any, Dict
import asyncio
import logging
from importlib import import_module

from state_transition_engine import StateTransitionEngine

from INANNA_AI import emotion_analysis, emotional_memory
from INANNA_AI.glm_integration import GLMIntegration
import emotional_state
from corpus_memory_logging import load_interactions, log_interaction

try:
    _settings_mod = import_module("config.settings")
    is_layer_enabled = getattr(_settings_mod, "is_layer_enabled", lambda name: True)
except Exception:  # pragma: no cover - missing config
    def is_layer_enabled(name: str) -> bool:  # type: ignore
        return True

import crown_decider
from task_profiling import classify_task
import servant_model_manager as smm


_EMOTION_KEYS = list(emotion_analysis.EMOTION_ARCHETYPES.keys())


_STATE_ENGINE = StateTransitionEngine()


def _detect_emotion(text: str) -> str:
    lowered = text.lower()
    for key in _EMOTION_KEYS:
        if key in lowered:
            return key
    return "neutral"


def _build_context(limit: int = 3) -> str:
    entries = load_interactions(limit=limit)
    if not entries:
        return "<no interactions>"
    parts = [e.get("input", "") for e in entries if e.get("input")]
    return "\n".join(parts)


async def _delegate(prompt: str, glm: GLMIntegration) -> str:
    return glm.complete(prompt)




def _apply_layer(message: str) -> tuple[str | None, str | None]:
    """Return layer-transformed text and model name if a layer is active."""
    layer_name = emotional_state.get_current_layer()
    if not layer_name or not is_layer_enabled(layer_name):
        return None, None
    try:
        layers_mod = import_module("INANNA_AI.personality_layers")
        registry = getattr(layers_mod, "REGISTRY", {})
    except Exception:
        return None, None
    cls = registry.get(layer_name)
    if cls is None:
        return None, None
    try:
        layer = cls()
        if hasattr(layer, "generate_response"):
            return str(layer.generate_response(message)), layer_name
        if hasattr(layer, "speak"):
            return str(layer.speak(message)), layer_name
    except Exception:
        logging.exception("layer %s failed", layer_name)
    return None, None


def crown_prompt_orchestrator(message: str, glm: GLMIntegration) -> Dict[str, Any]:
    """Return GLM or servant model reply with metadata."""
    emotion = _detect_emotion(message)
    archetype = emotion_analysis.emotion_to_archetype(emotion)
    weight = emotion_analysis.emotion_weight(emotion)
    state = _STATE_ENGINE.update_state(message)
    context = _build_context()
    prompt_body = f"{context}\n{message}" if context else message
    prompt = f"[{state}]\n{prompt_body}"

    layer_text, layer_model = _apply_layer(message)

    async def _process() -> tuple[str, str]:
        task_type = classify_task(message)
        model = crown_decider.recommend_llm(task_type, emotion)
        success = True
        try:
            if model == "glm":
                text = await _delegate(prompt, glm)
            else:
                text = await smm.invoke(model, message)
        except Exception:
            success = False
            crown_decider.record_result(model, False)
            log_interaction(message, {"emotion": emotion}, {"model": model}, "error")
            model = "glm"
            text = await _delegate(prompt, glm)
            crown_decider.record_result(model, True)
        affect = emotional_memory.score_affect(text, emotion)
        emotional_memory.record_interaction(
            emotional_memory.EmotionalMemoryNode(
                llm_name=model,
                prompt=message,
                response=text,
                emotion=emotion,
                success=success,
                archetype=archetype,
                affect=affect,
            )
        )
        if success:
            crown_decider.record_result(model, True)
        return text, model

    if layer_text is not None:
        text, model = layer_text, layer_model or "layer"
    else:
        text, model = asyncio.run(_process())

    return {
        "text": text,
        "model": model,
        "emotion": emotion,
        "archetype": archetype,
        "weight": weight,
        "state": state,
        "context_used": context,
    }


__all__ = ["crown_prompt_orchestrator"]
