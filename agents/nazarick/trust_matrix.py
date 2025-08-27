from __future__ import annotations

"""Trust classification and protocol lookup for Nazarick entities.

The :class:`TrustMatrix` records trust scores in a tiny SQLite database and
provides utilities to classify entities and determine the protocol to use for
interactions. Entity types and rank mappings mirror the Nazarick manifesto.
"""

from enum import Enum
from pathlib import Path
import sqlite3
from typing import Dict, Optional, Tuple, Any


class EntityType(str, Enum):
    """Supported entity categories."""

    NAZARICK = "nazarick"
    RIVAL = "rival"
    OUTSIDER = "outsider"


# Known Nazarick allies and their ranks
NAZARICK_RANKS: Dict[str, int] = {
    "shalltear": 1,
    "demiurge": 2,
    "cocytus": 3,
    "sebas": 4,
}

# Known rivals and their levels
RIVAL_RANKS: Dict[str, int] = {
    "clementine": 1,
    "slane": 2,
    "empire": 3,
    "kingdom": 4,
}

DEFAULT_TRUST = 5
"""Starting trust for entities without a recorded history."""


class TrustMatrix:
    """Track and evaluate trust for Nazarick interactions."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = (
            Path(db_path) if db_path is not None else Path("memory") / "trust.db"
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS trust (name TEXT PRIMARY KEY, score INTEGER)"
        )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    def classify(self, name: str) -> Tuple[EntityType, Optional[int]]:
        """Return entity category and rank if known."""

        key = name.lower()
        if key in NAZARICK_RANKS:
            return EntityType.NAZARICK, NAZARICK_RANKS[key]
        if key in RIVAL_RANKS:
            return EntityType.RIVAL, RIVAL_RANKS[key]
        return EntityType.OUTSIDER, None

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def get_trust(self, name: str) -> int:
        """Fetch trust score for ``name`` inserting baseline if absent."""

        key = name.lower()
        cur = self._conn.execute("SELECT score FROM trust WHERE name=?", (key,))
        row = cur.fetchone()
        if row is None:
            self.set_trust(key, DEFAULT_TRUST)
            return DEFAULT_TRUST
        return int(row[0])

    def set_trust(self, name: str, score: int) -> None:
        """Persist ``score`` for ``name``."""

        key = name.lower()
        self._conn.execute(
            "INSERT OR REPLACE INTO trust(name, score) VALUES(?, ?)", (key, int(score))
        )
        self._conn.commit()

    def delete(self, name: str) -> None:
        """Remove ``name`` from the trust store."""

        key = name.lower()
        self._conn.execute("DELETE FROM trust WHERE name=?", (key,))
        self._conn.commit()

    def all(self) -> Dict[str, int]:
        """Return mapping of all stored trust scores."""

        cur = self._conn.execute("SELECT name, score FROM trust")
        return {row[0]: int(row[1]) for row in cur.fetchall()}

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    def lookup_protocol(self, name: str) -> str:
        """Return the communication protocol for ``name``.

        Protocol names are derived from entity type, rank and trust score:

        - Nazarick allies use ``nazarick_rank{rank}_<low|mid|high>`` tiers.
        - Rivals use ``rival_level{rank}_<wrath|teaching>`` depending on trust.
        - Outsiders default to ``outsider_standard``.
        """

        etype, rank = self.classify(name)
        trust = self.get_trust(name)
        if etype is EntityType.NAZARICK:
            tier = "low"
            if trust >= 8:
                tier = "high"
            elif trust >= 5:
                tier = "mid"
            return f"nazarick_rank{rank}_{tier}"
        if etype is EntityType.RIVAL:
            intent = "teaching" if trust >= 5 else "wrath"
            return f"rival_level{rank}_{intent}"
        return "outsider_standard"

    # ------------------------------------------------------------------
    # Public evaluation helpers
    # ------------------------------------------------------------------
    def evaluate_entity(self, name: str) -> Dict[str, Any]:
        """Return structured evaluation metadata for ``name``.

        The result includes the entity classification, rank, current trust
        score and recommended protocol.
        """

        etype, rank = self.classify(name)
        trust = self.get_trust(name)
        protocol = self.lookup_protocol(name)
        return {
            "entity": name,
            "type": etype.value,
            "rank": rank,
            "trust": trust,
            "protocol": protocol,
        }

    def close(self) -> None:
        """Close the underlying database connection."""

        self._conn.close()


__all__ = [
    "EntityType",
    "NAZARICK_RANKS",
    "RIVAL_RANKS",
    "DEFAULT_TRUST",
    "TrustMatrix",
]
