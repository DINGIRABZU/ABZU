from __future__ import annotations

"""State machine driven by trust and entity category."""

from dataclasses import dataclass
from enum import Enum

from . import Magnitude, State


class EntityCategory(Enum):
    """Possible categories of interacting entities."""

    ALLY = "ally"
    NEUTRAL = "neutral"
    ENEMY = "enemy"


@dataclass
class AlbedoStateMachine:
    """Transition between alchemical states based on trust and entity."""

    state: State = State.NIGREDO

    def transition(self, trust: Magnitude, category: EntityCategory) -> State:
        """Update ``state`` from ``trust`` magnitude and ``category``.

        - ``ENEMY`` entities always reset the state to :class:`~albedo.State.NIGREDO`.
        - ``ALLY`` entities with trust ``>= 8`` reach :class:`~albedo.State.RUBEDO`.
        - Any entity with trust ``>= 5`` reaches :class:`~albedo.State.CITRINITAS`.
        - Any entity with trust ``>= 3`` reaches :class:`~albedo.State.ALBEDO`.
        - Otherwise the state remains :class:`~albedo.State.NIGREDO`.
        """

        if trust <= Magnitude.ZERO or category is EntityCategory.ENEMY:
            self.state = State.NIGREDO
        elif category is EntityCategory.ALLY and trust >= Magnitude.EIGHT:
            self.state = State.RUBEDO
        elif trust >= Magnitude.FIVE:
            self.state = State.CITRINITAS
        elif trust >= Magnitude.THREE:
            self.state = State.ALBEDO
        else:
            self.state = State.NIGREDO
        return self.state


__all__ = ["AlbedoStateMachine", "EntityCategory"]
