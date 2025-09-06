from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, Tuple

DEFAULT_DIRS = [
    "GENESIS",
    "IGNITION",
    "PRIME OPERATOR",
    "CODEX",
]


class DocumentRegistry:
    """Collect documents from doctrine directories.

    Parameters
    ----------
    roots:
        Optional iterable of directories to scan. When omitted, the registry
        searches the standard doctrine locations relative to the repository
        root.
    """

    def __init__(self, roots: Iterable[str | Path] | None = None) -> None:
        if roots is None:
            base = Path(__file__).resolve().parents[2]
            roots = [base / d for d in DEFAULT_DIRS]
        self._roots = [Path(r) for r in roots]

    def iter_documents(self) -> Iterator[Tuple[str, str]]:
        """Yield ``(path, text)`` pairs for markdown files under ``roots``."""
        for root in self._roots:
            if not root.exists():
                continue
            for path in root.rglob("*.md"):
                try:
                    yield str(path), path.read_text(encoding="utf-8")
                except Exception:  # pragma: no cover - file may be unreadable
                    continue

    def get_corpus(self) -> Dict[str, str]:
        """Return mapping of file paths to contents."""
        return {path: text for path, text in self.iter_documents()}
