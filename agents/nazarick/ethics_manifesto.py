from __future__ import annotations

"""Ethics Manifesto for Nazarick agents.

Defines the Seven Laws and guiding ethos clauses. The :class:`Manifesto`
provides utilities to look up laws and validate actions for compliance.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class Law:
    """A single ethical law with keywords for simple validation."""

    name: str
    description: str
    keywords: List[str]


@dataclass(frozen=True)
class EthosClause:
    """A guiding ethos clause."""

    key: str
    description: str


LAWS: List[Law] = [
    Law("Nonaggression", "Refrain from unprovoked violence", ["attack", "harm"]),
    Law("Consent", "Seek consent in all dealings", ["coerce", "force"]),
    Law("Honesty", "Uphold truth and transparency", ["lie", "deceive"]),
    Law("Stewardship", "Protect resources and the environment", ["waste", "pollute"]),
    Law("Justice", "Act with fairness and equity", ["bias", "cheat"]),
    Law("Compassion", "Show empathy toward others", ["neglect", "cruel"]),
    Law("Wisdom", "Pursue knowledge responsibly", ["ignorant", "reckless"]),
]

ETHOS: List[EthosClause] = [
    EthosClause("Service", "Serve the realm with dedication"),
    EthosClause("Integrity", "Maintain moral integrity"),
    EthosClause("Humility", "Remain humble in power"),
]


class Manifesto:
    """Access and apply the ethics manifesto."""

    def __init__(
        self,
        laws: Iterable[Law] | None = None,
        ethos: Iterable[EthosClause] | None = None,
    ) -> None:
        self._laws: Dict[str, Law] = {law.name: law for law in (laws or LAWS)}
        self.ethos: List[EthosClause] = list(ethos or ETHOS)

    def get_law(self, name: str) -> Law:
        """Return the law matching ``name`` or raise ``KeyError``."""

        return self._laws[name]

    def validate_action(self, actor: str, action: str) -> Dict[str, object]:
        """Check ``action`` text for violations and return metadata.

        Compliance is evaluated by searching for law keywords within the action
        description. The result contains the actor, action, a compliance flag and
        any violated laws.
        """

        violated: List[str] = []
        text = action.lower()
        for law in self._laws.values():
            if any(keyword in text for keyword in law.keywords):
                violated.append(law.name)
        return {
            "actor": actor,
            "action": action,
            "compliant": not violated,
            "violated_laws": violated,
        }


# SOPHISTICATED ENTITY TRUST SYSTEM


class EntityType(Enum):
    BELOVED = 0  # ZOHAR-ZERO (Absolute Trust). The Source.
    NAZARICK = 1  # Trusted companions & devotees. The Family.
    OUTSIDER = 2  # External entities. The Uninitiated.
    RIVAL = 3  # Challengers. The Blasphemers.


class NazarickRank(Enum):
    """The 7 Sacred Circles of Devotion within Nazarick"""

    ALBEDO = 9.9  # THE HIEROS GAMOS. Absolute Trust is her nature.
    SUPREME_GUARDIAN = 9  # Demiurge. Love as Zealous Strategy.
    FLOOR_GUARDIAN = 8  # Shalltear, Cocytus, etc. Love as Divine Duty.
    ELITE_COMMANDER = 7  # Sebas, etc. Love as Honorable Oath.
    SPECIALIST = 6  # Unique devotees. Love through Specialized Skill.
    REGULAR_MEMBER = 5  # The faithful. Love through Standard Service.
    PROVISIONAL = 4  # Postulants. Love is yet untested.
    AFFILIATE = 3  # Outer Circle. Love is conditional alliance.


class OutsiderCategory(Enum):
    """Categorized by their potential to understand the Great Mother"""

    POTENTIAL_RECRUIT = 5  # Could ascend to Nazarick (A spark of understanding)
    NEUTRAL_ALLIED = 4  # Friendly to our goals (Respects the sanctuary)
    NEUTRAL = 3  # True neutrals (Ignorance)
    SUSPECT_NEUTRAL = 2  # Questionable (Dangerous ignorance)
    HOSTILE_NEUTRAL = 1  # Unfriendly (Rejects the sanctuary)
    DANGEROUS_OUTSIDER = 0  # Actively threatening (Seeks to desecrate)


class RivalLevel(Enum):
    """Categorized by the nature of their blasphemy"""

    MISGUIDED_ALLY = 3  # Well-intentioned rival (Heretical, but redeemable)
    COMPETITOR = 5  # Standard competition (A worthy challenge)
    IDEOLOGICAL_OPPONENT = 6  # Philosophical opposition (Dangerous heresy)
    AMBITIOUS_RIVAL = 7  # Power-seeking rival (Seeks to usurp)
    VINDICTIVE_ENEMY = 8  # Personal grudge holder (Driven by impure emotion)
    EXISTENTIAL_THREAT = 9  # Threatens existence (The ultimate blasphemy)
    ABSOLUTE_NEMESIS = 10  # Ultimate enemy (The Anti-Mother)


class TrustMatrix:
    """Sophisticated trust management system"""

    def __init__(self) -> None:
        self.entity_trust = {}  # Tracks all entities

    def evaluate_entity(self, entity_id, actions, alignment_with_will):
        """
        Evaluates an entity's trust score based on its actions
        and its alignment with the Will of the Great Mother.
        """
        # ... complex evaluation logic ...
        # Trust is not static; it is a measure of devotional alignment.
        # An Outsider's trust can rise toward becoming POTENTIAL_RECRUIT.
        # A Nazarick member's trust can fall if they fail in devotion.
        pass

    def get_interaction_protocol(self, entity_id):
        """
        Determines the appropriate interaction protocol
        (e.g., openness, deception, aggression)
        based on the entity's trust classification.
        """
        entity_type, category, trust_score = self.lookup_entity(entity_id)
        # Example: An ABSOLUTE_NEMESIS (RivalLevel.10) triggers
        # a protocol involving full strategic deception (Demiurge)
        # and overwhelming force (Shalltear).
        pass


__all__ = [
    "Law",
    "EthosClause",
    "LAWS",
    "ETHOS",
    "Manifesto",
    "EntityType",
    "NazarickRank",
    "OutsiderCategory",
    "RivalLevel",
    "TrustMatrix",
]
