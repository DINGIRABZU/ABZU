"""Shared utilities for guardian agents."""

# @ip-sensitive: Ethics validation gatekeeper
from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Callable

from .event_bus import emit_event


def run_validated_task(
    manifesto: Any,
    trust_matrix: Any,
    actor: str,
    action: str,
    entity: str,
    task: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Execute ``task`` only if ethics validation passes.

    Validation and entity evaluation results are emitted to the global event
    bus. When the action violates the ethics manifesto the request is escalated
    to Cocytus for arbitration and ``None`` is returned.
    """

    ethics_result = manifesto.validate_action(actor, action)
    emit_event(actor, "validate_action", ethics_result)

    entity_result = trust_matrix.evaluate_entity(entity)
    emit_event(actor, "evaluate_entity", entity_result)

    if not ethics_result.get("compliant", False):
        from .cocytus.prompt_arbiter import arbitrate

        arbitrate(actor, action, entity_result)
        return None

    return task(*args, **kwargs)


__all__ = ["run_validated_task"]
