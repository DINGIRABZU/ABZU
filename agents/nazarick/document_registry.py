from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Iterator, Tuple


class DocumentRegistry:
    """Collect documents from configured directories."""

    def __init__(self, roots: Iterable[str | Path]) -> None:
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
