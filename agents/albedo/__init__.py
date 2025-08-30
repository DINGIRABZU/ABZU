"""Albedo agent messaging utilities and vision hooks."""

from __future__ import annotations

__version__ = "0.1.0"

from agents.nazarick.ethics_manifesto import Manifesto
from agents.nazarick.trust_matrix import TrustMatrix
from ..guardian import run_validated_task

from .messaging import compose_message_nazarick, compose_message_rival
from .trust import update_trust
from .vision import consume_detections, current_avatar

_manifesto = Manifesto()
_trust_matrix = TrustMatrix()
_AGENT = "albedo"


def execute_task(action: str, entity: str, task, *args, **kwargs):
    """Run ``task`` after ethics and trust checks."""
    return run_validated_task(
        _manifesto, _trust_matrix, _AGENT, action, entity, task, *args, **kwargs
    )


__all__ = [
    "compose_message_nazarick",
    "compose_message_rival",
    "update_trust",
    "consume_detections",
    "current_avatar",
    "execute_task",
]
