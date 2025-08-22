"""Core package exposing primary services."""

from __future__ import annotations

from .contracts import EmotionAnalyzerService, MemoryLoggerService
from .emotion_analyzer import EmotionAnalyzer
from .memory_logger import MemoryLogger

__all__ = [
    "EmotionAnalyzer",
    "MemoryLogger",
    "EmotionAnalyzerService",
    "MemoryLoggerService",
]
