"""Core package exposing primary services.

Provides shortcut imports for frequently used components.
"""

# Ensures `core` is recognized as a package when installed in editable mode.

from __future__ import annotations

from .config import load_config
from .contracts import EmotionAnalyzerService, MemoryLoggerService
from .emotion_analyzer import EmotionAnalyzer
from .feedback_logging import append_feedback, load_feedback
from .memory_logger import MemoryLogger
from .task_profiler import TaskProfiler

__all__ = [
    "EmotionAnalyzer",
    "MemoryLogger",
    "EmotionAnalyzerService",
    "MemoryLoggerService",
    "append_feedback",
    "load_feedback",
    "load_config",
    "TaskProfiler",
]
