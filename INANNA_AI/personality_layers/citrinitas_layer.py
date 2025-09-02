"""Illumination phase personality layer."""

from __future__ import annotations


class CitrinitasPersonality:
    """Guide with wisdom of the golden dawn."""

    def speak(self, message: str) -> str:
        """Return ``message`` bathed in radiant light."""
        return f"Citrinitas speaks in golden clarity: {message}"

    def choose_path(self, context: str) -> str:
        """Suggest enlightenment via ``context``."""
        return f"Following {context}, the sun of understanding rises."


__all__ = ["CitrinitasPersonality"]
