from __future__ import annotations

"""Albedo personality layer combining state context with the GLM."""

from .alchemical_persona import AlchemicalPersona, State
from .glm_integration import GLMIntegration
from . import state_contexts
from ...emotion_analysis import get_emotion_and_tone
import qnl_engine


class AlbedoPersonality:
    """Generate text according to the current alchemical state."""

    def __init__(
        self,
        integration: GLMIntegration | None = None,
        persona: AlchemicalPersona | None = None,
    ) -> None:
        self._persona = persona or AlchemicalPersona()
        self._glm = integration or GLMIntegration()

    @property
    def state(self) -> str:
        """Return the name of the current state."""
        return self._persona.state.value

    def generate_response(self, text: str, *, quantum_context: str | None = None) -> str:
        """Generate a GLM response for ``text``."""
        entity, triggers = self._persona.detect_state_trigger(text)
        emotion, tone = get_emotion_and_tone()
        if quantum_context is None:
            qnl_engine.apply_emotional_quantum_state(emotion, text)
            quantum_context = f"{emotion}:{tone}"
        template = state_contexts.CONTEXTS.get(self._persona.state.value, "{text}")
        ctx = {
            "text": text,
            "entity": entity,
            "triggers": ",".join(sorted(triggers)) if triggers else "",
            "qcontext": quantum_context or "",
        }
        prompt = template.format(**ctx)
        reply = self._glm.complete(prompt, quantum_context=quantum_context)
        self._persona.update_metrics(triggers)
        self._persona.advance()
        return reply


__all__ = ["AlbedoPersonality", "AlchemicalPersona", "State"]
