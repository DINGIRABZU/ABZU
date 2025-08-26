from __future__ import annotations

"""Entity classification with trust scoring and persistence."""

import json
from pathlib import Path
from typing import Dict, Tuple

# File storing trust histories
TRUST_REGISTRY = Path(__file__).with_name("trust_registry.json")

# Known Nazarick roles with their baseline trust scores
NAZARICK_ROLES: Dict[str, int] = {
    "ainz": 10,
    "albedo": 9,
    "demiurge": 8,
}

# Entities considered rivals of Nazarick and their trust scores
RIVALS: Dict[str, int] = {
    "clementine": 1,
    "slane": 2,
}

# Default trust for outsiders not listed above
DEFAULT_OUTSIDER_TRUST = 5


def detect_entity(name: str) -> Tuple[str, int]:
    """Classify ``name`` and record its trust score.

    Parameters
    ----------
    name:
        Entity name to classify.

    Returns
    -------
    tuple of (category, trust)
        Category is ``"nazarick"``, ``"rival"`` or ``"outsider"``.
    """

    key = name.lower()
    if key in NAZARICK_ROLES:
        category = "nazarick"
        trust = NAZARICK_ROLES[key]
    elif key in RIVALS:
        category = "rival"
        trust = RIVALS[key]
    else:
        category = "outsider"
        trust = DEFAULT_OUTSIDER_TRUST
    _record_trust(key, trust)
    return category, trust


def _record_trust(name: str, trust: int) -> None:
    """Append ``trust`` for ``name`` to the registry file."""

    data: Dict[str, list[int]] = {}
    if TRUST_REGISTRY.exists():
        try:
            data = json.loads(TRUST_REGISTRY.read_text())
        except json.JSONDecodeError:
            data = {}
    history = data.setdefault(name, [])
    history.append(trust)
    TRUST_REGISTRY.write_text(json.dumps(data, indent=2))


__all__ = [
    "detect_entity",
    "TRUST_REGISTRY",
    "NAZARICK_ROLES",
    "RIVALS",
    "DEFAULT_OUTSIDER_TRUST",
]
