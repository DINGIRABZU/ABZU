from __future__ import annotations

"""Wrapper around corpus memory logging helpers."""

from typing import Any, Dict, List

from corpus_memory_logging import (
    log_interaction,
    load_interactions,
    log_ritual_result,
)


class MemoryLogger:
    """Provide methods for storing interaction history."""

    def log_interaction(self, text: str, meta: Dict[str, Any], result: Dict[str, Any], status: str) -> None:
        log_interaction(text, meta, result, status)

    def load_interactions(self) -> List[Dict[str, Any]]:
        return load_interactions()

    def log_ritual_result(self, name: str, steps: List[Any]) -> None:
        log_ritual_result(name, steps)

