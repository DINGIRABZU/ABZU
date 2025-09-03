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

from __future__ import annotations

__version__ = "0.2.2"

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

REMEDIATION_HINTS = {
    IssueType.DEPENDENCY: "Install missing packages or verify the environment.",
    IssueType.LOGIC: "Inspect the stack trace and fix the underlying code logic.",
    IssueType.EXTERNAL: "Check network connectivity and external service status.",
}


def _match(keywords: Iterable[str], text: str) -> bool:
    return any(k in text for k in keywords)


def analyze_text(log_text: str) -> tuple[IssueType, str]:
    """Return issue classification and remediation hint for ``log_text``."""

    normalized = log_text.lower()
    if _match(_DEPENDENCY_KEYWORDS, normalized):
        issue = IssueType.DEPENDENCY
    elif _match(_LOGIC_KEYWORDS, normalized):
        issue = IssueType.LOGIC
    else:
        issue = IssueType.EXTERNAL
    return issue, REMEDIATION_HINTS[issue]


def analyze_file(path: str | Path) -> tuple[IssueType, str]:
    """Read ``path`` and classify its contents with a remediation hint."""

    text = Path(path).read_text(errors="ignore")
    return analyze_text(text)


__all__ = ["IssueType", "analyze_text", "analyze_file"]
