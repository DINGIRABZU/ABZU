from __future__ import annotations

"""Completion phase personality layer."""

class RubedoPersonality:
    """Celebrate fiery transformation."""

    def speak(self, message: str) -> str:
        """Return an exalted form of ``message``."""
        return f"Rubedo proclaims with blazing heart: {message}"

    def choose_path(self, context: str) -> str:
        """Reveal the triumphant route through ``context``."""
        return f"Along {context}, the crimson phoenix ascends."

__all__ = ["RubedoPersonality"]
