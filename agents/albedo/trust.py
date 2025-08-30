# pydocstyle: skip-file
"""Trust adjustment and interaction logging for Albedo dialogues."""

from __future__ import annotations

__version__ = "0.1.1"

from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, Tuple, Union

from agents import emit_event

from albedo import Magnitude, State
from albedo.state_machine import AlbedoStateMachine, EntityCategory
from memory.trust_registry import (
    NAZARICK_ROLES,
    RIVALS,
    DEFAULT_OUTSIDER_TRUST,
)

TRUST_SCORES: Dict[str, int] = {}
"""In-memory tracker of current trust scores per entity."""

LAST_INTERACTION: Dict[str, datetime] = {}
"""Last interaction timestamp for each entity."""

LOG_FILE = Path("logs/albedo_interactions.jsonl")
"""Location for dialogue interaction records."""

TRUST_FILE = Path("logs/trust_scores.json")
"""Persistence file for trust scores and timestamps."""


def _now() -> datetime:
    """Return current UTC time.

    Wrapped for easier testing.
    """
    return datetime.utcnow()


def _load_scores() -> None:
    """Populate :data:`TRUST_SCORES` and :data:`LAST_INTERACTION` from disk."""
    if not TRUST_FILE.exists():
        return
    try:
        data = json.loads(TRUST_FILE.read_text())
    except json.JSONDecodeError:
        return
    for key, info in data.items():
        try:
            TRUST_SCORES[key] = int(info["trust"])
            LAST_INTERACTION[key] = datetime.fromisoformat(info["last"])
        except (KeyError, ValueError):
            continue


def _save_scores() -> None:
    """Write current trust state to :data:`TRUST_FILE`."""
    TRUST_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        key: {"trust": score, "last": LAST_INTERACTION[key].isoformat()}
        for key, score in TRUST_SCORES.items()
    }
    TRUST_FILE.write_text(json.dumps(data, indent=2))


def _category_and_baseline(entity: str) -> Tuple[EntityCategory, int]:
    """Return entity category and starting trust score."""
    key = entity.lower()
    if key in NAZARICK_ROLES:
        return EntityCategory.ALLY, NAZARICK_ROLES[key]
    if key in RIVALS:
        return EntityCategory.ENEMY, RIVALS[key]
    return EntityCategory.NEUTRAL, DEFAULT_OUTSIDER_TRUST


def update_trust(
    entity: str, outcome: Union[str, bool], decay_seconds: float | None = None
) -> Tuple[Magnitude, State]:
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

    if decay_seconds is not None:
        _apply_decay(key, baseline, decay_seconds)

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
    LAST_INTERACTION[key] = _now()
    magnitude = Magnitude(trust)
    state_machine = AlbedoStateMachine()
    state = state_machine.transition(magnitude, category)
    _log_interaction(entity, outcome_str, magnitude, state)
    _save_scores()
    emit_event(
        "albedo",
        "trust_update",
        {
            "entity": entity,
            "outcome": outcome_str,
            "magnitude": int(magnitude),
            "state": state.value,
        },
    )
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


def _apply_decay(key: str, baseline: int, decay_seconds: float) -> None:
    """Reduce trust toward ``baseline`` based on elapsed time."""
    last = LAST_INTERACTION.get(key)
    if not last:
        return
    now = _now()
    elapsed = (now - last).total_seconds()
    steps = int(elapsed // decay_seconds)
    if steps <= 0:
        return
    trust = TRUST_SCORES.get(key, baseline)
    if trust > baseline:
        trust = max(baseline, trust - steps)
    elif trust < baseline:
        trust = min(baseline, trust + steps)
    TRUST_SCORES[key] = trust
    LAST_INTERACTION[key] = last + timedelta(seconds=steps * decay_seconds)
    _save_scores()


_load_scores()


__all__ = ["update_trust", "TRUST_SCORES", "LOG_FILE", "TRUST_FILE"]
