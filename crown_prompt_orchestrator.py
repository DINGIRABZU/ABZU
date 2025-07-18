from __future__ import annotations

"""Lightweight orchestrator for the Crown console."""

from typing import Any, Dict
import asyncio

from state_transition_engine import StateTransitionEngine

from INANNA_AI.glm_integration import GLMIntegration
from INANNA_AI import emotion_analysis
from task_profiling import classify_task
from corpus_memory_logging import load_interactions, log_interaction
import servant_model_manager as smm
from INANNA_AI import emotional_memory
import crown_decider


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




def crown_prompt_orchestrator(message: str, glm: GLMIntegration) -> Dict[str, Any]:
    """Return GLM or servant model reply with metadata."""
    emotion = _detect_emotion(message)
    archetype = emotion_analysis.emotion_to_archetype(emotion)
    weight = emotion_analysis.emotion_weight(emotion)
    state = _STATE_ENGINE.update_state(message)
    context = _build_context()
    prompt_body = f"{context}\n{message}" if context else message
    prompt = f"[{state}]\n{prompt_body}"

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
