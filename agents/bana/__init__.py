"""Bana bio-adaptive narrator agent."""

from __future__ import annotations

from agents.nazarick.ethics_manifesto import Manifesto
from agents.nazarick.trust_matrix import TrustMatrix
from ..guardian import run_validated_task

from .bio_adaptive_narrator import generate_story

_manifesto = Manifesto()
_trust_matrix = TrustMatrix()
_AGENT = "bana"


def execute_task(action: str, entity: str, task, *args, **kwargs):
    """Run ``task`` after ethics and trust checks."""

    return run_validated_task(
        _manifesto, _trust_matrix, _AGENT, action, entity, task, *args, **kwargs
    )


__all__ = ["generate_story", "execute_task"]
