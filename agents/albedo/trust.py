from __future__ import annotations

"""Trust adjustment and interaction logging for Albedo dialogues."""

from pathlib import Path
import json
from typing import Dict, Tuple, Union

from albedo import Magnitude, State
from albedo.state_machine import AlbedoStateMachine, EntityCategory
from memory.trust_registry import (
    NAZARICK_ROLES,
    RIVALS,
    DEFAULT_OUTSIDER_TRUST,
)

TRUST_SCORES: Dict[str, int] = {}
"""In-memory tracker of current trust scores per entity."""

LOG_FILE = Path("logs/albedo_interactions.jsonl")
"""Location for dialogue interaction records."""


def _category_and_baseline(entity: str) -> Tuple[EntityCategory, int]:
    """Return entity category and starting trust score."""
    key = entity.lower()
    if key in NAZARICK_ROLES:
        return EntityCategory.ALLY, NAZARICK_ROLES[key]
    if key in RIVALS:
        return EntityCategory.ENEMY, RIVALS[key]
    return EntityCategory.NEUTRAL, DEFAULT_OUTSIDER_TRUST


def update_trust(entity: str, outcome: Union[str, bool]) -> Tuple[Magnitude, State]:
    """Adjust trust for ``entity`` based on interaction ``outcome``.

    Parameters
    ----------
    entity:
        Name of the interacting entity.
    outcome:
        Interaction result. ``True``/``"positive"`` increases trust, while
        ``False``/``"negative"`` decreases it.

    Returns
    -------
    tuple of (:class:`~albedo.Magnitude`, :class:`~albedo.State`)
        Updated trust magnitude and resulting alchemical state.
    """
    key = entity.lower()
    category, baseline = _category_and_baseline(entity)
    trust = TRUST_SCORES.get(key, baseline)

    is_positive = outcome in (True, "positive", "success")
    is_negative = outcome in (False, "negative", "failure")
    if is_positive:
        trust = min(Magnitude.TEN, trust + 1)
        outcome_str = "positive"
    elif is_negative:
        trust = max(Magnitude.ZERO, trust - 1)
        outcome_str = "negative"
    else:
        outcome_str = "neutral"

    TRUST_SCORES[key] = trust
    magnitude = Magnitude(trust)
    state_machine = AlbedoStateMachine()
    state = state_machine.transition(magnitude, category)
    _log_interaction(entity, outcome_str, magnitude, state)
    return magnitude, state


def _log_interaction(
    entity: str, outcome: str, magnitude: Magnitude, state: State
) -> None:
    """Append a dialogue interaction to :data:`LOG_FILE`."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "entity": entity,
        "outcome": outcome,
        "magnitude": int(magnitude),
        "state": state.value,
    }
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


__all__ = ["update_trust", "TRUST_SCORES", "LOG_FILE"]
