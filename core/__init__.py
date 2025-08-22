from __future__ import annotations

"""Core package exposing primary services."""

from .emotion_analyzer import EmotionAnalyzer
from .memory_logger import MemoryLogger
from .contracts import EmotionAnalyzerService, MemoryLoggerService

__all__ = [
    'EmotionAnalyzer',
    'MemoryLogger',
    'EmotionAnalyzerService',
    'MemoryLoggerService',
]
