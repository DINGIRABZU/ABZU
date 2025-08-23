from __future__ import annotations

"""Utilities for inspecting repository code.

This module enumerates Python files in the repository, extracts short snippets
and writes them to ``audit_logs/code_analysis.txt`` for later review.
"""

from pathlib import Path
from typing import Iterable, List

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_FILE = REPO_ROOT / "audit_logs" / "code_analysis.txt"


def iter_modules(root: Path | None = None) -> Iterable[Path]:
    """Yield Python modules under *root*.

    Files in hidden directories or virtual environments are ignored.
    """

    root = root or REPO_ROOT
    for path in root.rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if "venv" in path.parts:
            continue
        yield path


def get_snippet(path: Path, lines: int = 5) -> str:
    """Return the first ``lines`` lines from ``path``.

    Parameters
    ----------
    path:
        The module path.
    lines:
        Number of lines to include from the top of the file.
    """

    text = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(text[:lines])


def analyze_repository(root: Path | None = None, limit: int = 20) -> List[str]:
    """Write a simple code analysis log and return collected snippets.

    Parameters
    ----------
    root:
        Repository root to search from. Defaults to the project root.
    limit:
        Maximum number of modules to log. This avoids excessively large files.
    """

    root = root or REPO_ROOT
    modules = list(iter_modules(root))[:limit]
    snippets: List[str] = []
    for module in modules:
        snippet = get_snippet(module)
        rel = module.relative_to(root)
        snippets.append(f"{rel}: {snippet}")

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_FILE.write_text("\n".join(snippets), encoding="utf-8")
    return snippets

