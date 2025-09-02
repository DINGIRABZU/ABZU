"""Helpers to compose prompts for Albedo's enlightened responses."""

from __future__ import annotations

from typing import Callable, Dict

from .alchemical_persona import AlchemicalPersona, State

# Human readable fragments describing each state. All phases of the
# alchemical cycle must be represented here so callers can format
# prompts without conditional checks.
STATE_DESCRIPTIONS: Dict[str, str] = {
    "nigredo": "desc_nigredo",
    "albedo": "desc_albedo",
    "rubedo": "desc_rubedo",
    "citrinitas": "desc_citrinitas",
}


def _compose_deity(state: State, text: str) -> str:
    """Return prompt line for deity entities."""
    desc = STATE_DESCRIPTIONS[state.value]
    return f"DEITY-{state.value}-{desc}:{text}"


def _compose_person(state: State, text: str) -> str:
    """Return prompt line for person entities."""
    desc = STATE_DESCRIPTIONS[state.value]
    return f"PERSON-{state.value}-{desc}:{text}"


def _compose_object(state: State, text: str) -> str:
    """Return prompt line for object entities."""
    desc = STATE_DESCRIPTIONS[state.value]
    return f"OBJECT-{state.value}-{desc}:{text}"


_COMPOSERS: Dict[str, Callable[[State, str], str]] = {
    "deity": _compose_deity,
    "person": _compose_person,
    "object": _compose_object,
}


def _build_enlightened_prompt(persona: AlchemicalPersona, text: str) -> str:
    """Return a composed prompt based on ``persona``'s entity detection."""
    entity, _ = persona.detect_state_trigger(text)
    composer = _COMPOSERS.get(entity, _compose_object)
    return composer(persona.state, text)


__all__ = ["_build_enlightened_prompt", "STATE_DESCRIPTIONS"]
