# pydocstyle: skip-file
"""Ethics Manifesto for Nazarick agents.

Defines the Seven Laws and guiding ethos clauses. The :class:`Manifesto`
provides utilities to look up laws and validate actions for compliance.
"""

from __future__ import annotations

__version__ = "0.1.1"

from dataclasses import dataclass
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

    # Use ``name`` for consistency with :class:`Law`.
    name: str
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


__all__ = ["Law", "EthosClause", "LAWS", "ETHOS", "Manifesto"]
