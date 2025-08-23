"""Core package exposing primary services."""

from __future__ import annotations

from .config import load_config
from .contracts import EmotionAnalyzerService, MemoryLoggerService
from .emotion_analyzer import EmotionAnalyzer
from .feedback_logging import append_feedback, load_feedback
from .memory_logger import MemoryLogger

__all__ = [
    "EmotionAnalyzer",
    "MemoryLogger",
    "EmotionAnalyzerService",
    "MemoryLoggerService",
    "append_feedback",
    "load_feedback",
    "load_config",
]
