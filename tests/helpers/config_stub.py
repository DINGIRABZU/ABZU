from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace


def build_settings():
    """Return a config-like object with required attributes for tests."""
    return SimpleNamespace(
        vector_db_path=Path("/tmp"),
        crown_tts_backend="gtts",
        voice_avatar_config_path=None,
        retrain_threshold=10,
        llm_rotation_period=300,
        llm_max_failures=3,
        feedback_novelty_threshold=0.5,
        feedback_coherence_threshold=0.5,
    )
