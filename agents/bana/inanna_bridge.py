from __future__ import annotations

"""Bridge structured INANNA interactions into Bana's narrative engine."""

from typing import Mapping, Any

from agents.event_bus import emit_event

from .bio_adaptive_narrator import generate_story


def process_interaction(interaction: Mapping[str, Any]) -> str:
    """Process a structured interaction from INANNA.

    Parameters
    ----------
    interaction:
        Mapping containing at minimum a ``bio_stream`` sequence of floats.
    """

    bio_stream = interaction.get("bio_stream", [])
    story = generate_story(bio_stream)
    emit_event("inanna", "bana_narrative", {"length": len(story)})
    return story


__all__ = ["process_interaction"]
