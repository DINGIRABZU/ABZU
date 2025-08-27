from __future__ import annotations

"""Loader utilities for Nazarick persona profiles."""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Any

import yaml


@lru_cache(maxsize=1)
def load_persona_profiles() -> Dict[str, Dict[str, Any]]:
    """Return mapping of agent IDs to persona profile data.

    Profiles are defined in ``persona_profiles.yaml`` with fields:
    ``agent_id``, ``floor``, ``channel``, ``voice_style`` and
    ``chakra_alignment``.
    """

    path = Path(__file__).with_name("persona_profiles.yaml")
    data = yaml.safe_load(path.read_text())
    return {item["agent_id"]: item for item in data}


__all__ = ["load_persona_profiles"]

