"""RAZAR agents."""

__version__ = "0.1.0"

from agents.nazarick.ethics_manifesto import Manifesto
from agents.nazarick.trust_matrix import TrustMatrix
from ..guardian import run_validated_task

from .remote_loader import (
    load_remote_agent,
    load_remote_agent_from_git,
    load_remote_gpt_agent,
)
from .lifecycle_bus import LifecycleBus
from . import pytest_runner

_manifesto = Manifesto()
_trust_matrix = TrustMatrix()
_AGENT = "razar"


def execute_task(action: str, entity: str, task, *args, **kwargs):
    """Run ``task`` after ethics and trust checks."""

    return run_validated_task(
        _manifesto, _trust_matrix, _AGENT, action, entity, task, *args, **kwargs
    )


__all__ = [
    "load_remote_agent",
    "load_remote_agent_from_git",
    "load_remote_gpt_agent",
    "LifecycleBus",
    "execute_task",
    "pytest_runner",
]
