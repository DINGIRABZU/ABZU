"""Wrapper around corpus memory logging helpers."""

from __future__ import annotations

from typing import Any, Dict, List, cast

from corpus_memory_logging import load_interactions, log_interaction, log_ritual_result

from .contracts import MemoryLoggerService


class MemoryLogger(MemoryLoggerService):  # type: ignore[misc]
    """Provide methods for storing interaction history."""

    def log_interaction(
        self, text: str, meta: Dict[str, Any], result: Dict[str, Any], status: str
    ) -> None:
        log_interaction(text, meta, result, status)

    def load_interactions(self) -> List[Dict[str, Any]]:
        return cast(List[Dict[str, Any]], load_interactions())

    def log_ritual_result(self, name: str, steps: List[Any]) -> None:
        log_ritual_result(name, steps)
