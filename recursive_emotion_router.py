from __future__ import annotations

"""Recursive cycle through emotional processing stages."""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Protocol
import json

import vector_memory
import cortex_memory
import cortex_sigil_logic


class SpiralNode(Protocol):
    """Protocol describing required node interface."""

    children: Iterable["SpiralNode"]

    def ask(self) -> None:
        ...

    def feel(self) -> None:
        ...

    def symbolize(self) -> None:
        ...

    def pause(self) -> None:
        ...

    def reflect(self) -> None:
        ...

    def decide(self) -> Dict[str, Any]:
        ...


def _state_text(node: SpiralNode) -> str:
    """Return JSON string describing ``node`` state."""
    if is_dataclass(node):
        state = asdict(node)
    else:
        try:
            state = dict(node.__dict__)
        except Exception:  # pragma: no cover - fallback for exotic objects
            state = {}
    return json.dumps(state, default=str)


_STAGES = (
    "ask",
    "feel",
    "symbolize",
    "pause",
    "reflect",
    "decide",
)


def _cycle(node: SpiralNode) -> Dict[str, Any]:
    """Execute all spiral stages once and log after each."""
    decision: Dict[str, Any] | None = None
    for stage in _STAGES:
        result = getattr(node, stage)()
        if stage == "decide":
            decision = result if isinstance(result, dict) else node.decide()
            text = str(decision.get("event") or decision.get("text") or "")
            triggers = cortex_sigil_logic.interpret_sigils(text)
            if triggers:
                decision["sigil_triggers"] = triggers
        vector_memory.add_vector(
            _state_text(node), {"type": "spiral_step", "stage": stage}
        )
    return decision or {}


def route(node: SpiralNode, depth: int = 1) -> Dict[str, Any]:
    """Process ``node`` through the spiral cycle recursively."""
    result = _cycle(node)
    cortex_memory.record_spiral(node, result)
    if depth > 1:
        for child in getattr(node, "children", []):
            route(child, depth - 1)
    return result


__all__ = ["SpiralNode", "route"]
