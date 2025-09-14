"""Bridge structured INANNA interactions into Bana's narrative engine."""

from __future__ import annotations

from typing import Mapping, Any

__version__ = "0.0.2"

from bana import narrative
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
    payload = {"story": story, "length": len(story)}
    narrative.emit("bana", "bio_story", payload, target_agent="albedo")
    return story


__all__ = ["process_interaction", "__version__"]
