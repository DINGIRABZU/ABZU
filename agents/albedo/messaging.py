from __future__ import annotations

"""Compose messages for Nazarick entities based on rank and trust."""

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
def _load_rival_templates() -> Dict[str, Dict]:
    """Load rival messaging templates from YAML."""

    path = Path(__file__).with_name("rival_templates.yaml")
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


def compose_message_rival(entity: str, state: State, magnitude: Magnitude) -> str:
    """Return a message for a rival based on ``state`` and ``magnitude``.

    Supports teaching messages when ``state`` is :class:`~albedo.State.CITRINITAS`
    and wrath messages when ``state`` is :class:`~albedo.State.NIGREDO`.
    """

    templates = _load_rival_templates()
    entity_key = entity.lower()
    try:
        level = templates["entities"][entity_key]
    except KeyError as exc:
        raise KeyError(f"Unknown rival entity: {entity}") from exc

    if state is State.CITRINITAS:
        category = "teaching"
    elif state is State.NIGREDO:
        category = "wrath"
    else:
        raise ValueError(f"Unsupported state: {state}")

    state_templates: Dict[str, Dict[str, str]] = templates["templates"][category][
        str(level)
    ]
    trust_value = int(magnitude)
    level_key = max(
        int(k) for k in state_templates.keys() if int(k) <= trust_value
    )
    template = state_templates[str(level_key)]
    return template.format(entity=entity, state=state.value, trust=trust_value)


__all__ = ["compose_message_nazarick", "compose_message_rival"]
