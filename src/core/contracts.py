"""Protocol definitions for cross-module services."""

from __future__ import annotations

from typing import Any, Dict, List, Protocol


class EmotionAnalyzerService(Protocol):
    """Analyze emotional content and maintain mood state."""

    def analyze(self, emotion: str) -> Dict[str, Any]: ...
    def update_mood(self, emotion: str) -> None: ...


class MemoryLoggerService(Protocol):
    """Persist interaction history and ritual results."""

    def log_interaction(
        self, text: str, meta: Dict[str, Any], result: Dict[str, Any], status: str
    ) -> None: ...
    def load_interactions(self) -> List[Dict[str, Any]]: ...
    def log_ritual_result(self, name: str, steps: List[Any]) -> None: ...
