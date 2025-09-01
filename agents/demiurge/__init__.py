"""Demiurge agent modules."""

__version__ = "0.1.0"

from agents.nazarick.ethics_manifesto import Manifesto
from agents.nazarick.trust_matrix import TrustMatrix
from ..guardian import run_validated_task

_manifesto = Manifesto()
_trust_matrix = TrustMatrix()
_AGENT = "demiurge"


def execute_task(action: str, entity: str, task, *args, **kwargs):
    """Run ``task`` after ethics and trust checks."""

    return run_validated_task(
        _manifesto, _trust_matrix, _AGENT, action, entity, task, *args, **kwargs
    )


__all__ = ["execute_task"]
