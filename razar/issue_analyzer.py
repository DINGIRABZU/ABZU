from __future__ import annotations

__version__ = "0.2.2"

"""Simple heuristics for classifying failure logs.

The :mod:`issue_analyzer` inspects failure logs and attempts to label the
underlying issue.  Three categories are supported:

``dependency``
    Missing modules or packages required by the component.
``logic``
    Exceptions that indicate a bug or incorrect assumption in the code.
``external``
    Network outages, remote service errors, or unclassified failures.
"""

from enum import Enum
from pathlib import Path
from typing import Iterable


class IssueType(str, Enum):
    """Supported issue categories."""

    DEPENDENCY = "dependency"
    LOGIC = "logic"
    EXTERNAL = "external"


# Keywords are intentionally lightweight so the analyzer remains fast and has
# no external dependencies.  The lists can be expanded as new failure modes are
# observed.
_DEPENDENCY_KEYWORDS: Iterable[str] = [
    "importerror",
    "modulenotfounderror",
    "no module named",
    "dependencyerror",
    "cannot import",
]

_LOGIC_KEYWORDS: Iterable[str] = [
    "assertionerror",
    "typeerror",
    "valueerror",
    "keyerror",
    "indexerror",
    "attributeerror",
]

_EXTERNAL_KEYWORDS: Iterable[str] = [
    "connectionerror",
    "timeout",
    "dns",
    "503",
    "gateway",
]


def _match(keywords: Iterable[str], text: str) -> bool:
    return any(k in text for k in keywords)


def analyze_text(log_text: str) -> IssueType:
    """Return an :class:`IssueType` classification for ``log_text``."""

    normalized = log_text.lower()
    if _match(_DEPENDENCY_KEYWORDS, normalized):
        return IssueType.DEPENDENCY
    if _match(_LOGIC_KEYWORDS, normalized):
        return IssueType.LOGIC
    # External issues are the fallback when no other keywords match.
    return IssueType.EXTERNAL


def analyze_file(path: str | Path) -> IssueType:
    """Read ``path`` and classify its contents."""

    text = Path(path).read_text(errors="ignore")
    return analyze_text(text)


__all__ = ["IssueType", "analyze_text", "analyze_file"]
