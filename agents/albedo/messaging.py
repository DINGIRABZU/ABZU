from __future__ import annotations

"""Compose messages for Nazarick entities and outsiders based on trust."""

from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml

from albedo import State, Magnitude


@lru_cache(maxsize=1)
def _load_templates() -> Dict[str, Dict]:
    """Load Nazarick messaging templates from YAML."""

    path = Path(__file__).with_name("nazarick_templates.yaml")
    data = yaml.safe_load(path.read_text())
    return data


@lru_cache(maxsize=1)
def _load_outsider_templates() -> Dict[str, Dict]:
    """Load outsider messaging templates from YAML."""

    path = Path(__file__).with_name("outsider_templates.yaml")
    data = yaml.safe_load(path.read_text())
    return data


def compose_message_nazarick(entity: str, state: State, magnitude: Magnitude) -> str:
    """Return formatted message for ``entity`` given ``state`` and ``magnitude``.

    Parameters
    ----------
    entity:
        Name of the entity (case insensitive).
    state:
        Current alchemical :class:`~albedo.State`.
    magnitude:
        Trust level as :class:`~albedo.Magnitude`.
    """

    templates = _load_templates()
    entity_key = entity.lower()
    try:
        rank = templates["entities"][entity_key]
    except KeyError as exc:
        raise KeyError(f"Unknown entity: {entity}") from exc

    trust_templates: Dict[str, str] = templates["templates"][str(rank)]
    trust_value = int(magnitude)
    # Choose the highest defined trust level not exceeding the given magnitude
    level = max(int(k) for k in trust_templates.keys() if int(k) <= trust_value)
    template = trust_templates[str(level)]
    return template.format(entity=entity, state=state.value, trust=trust_value)


def compose_message_outsider(entity: str, state: State, magnitude: Magnitude) -> str:
    """Return outsider message in analytic, diplomatic or warning tone.

    Parameters
    ----------
    entity:
        Name of the outsider (case insensitive).
    state:
        Current alchemical :class:`~albedo.State`.
    magnitude:
        Trust level as :class:`~albedo.Magnitude`.
    """

    templates = _load_outsider_templates()
    entity_key = entity.lower()
    try:
        category = templates["entities"][entity_key]
    except KeyError as exc:
        raise KeyError(f"Unknown outsider entity: {entity}") from exc

    trust_value = int(magnitude)
    if trust_value <= 3:
        tone = "warning"
    elif trust_value <= 7:
        tone = "analytic"
    else:
        tone = "diplomatic"

    template = templates["templates"][category][tone]
    return template.format(entity=entity, state=state.value, trust=trust_value)


__all__ = ["compose_message_nazarick", "compose_message_outsider"]
