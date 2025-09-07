from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

DEFAULT_DIRS = [
    "GENESIS",
    "IGNITION",
    "PRIME OPERATOR",
    "CODEX",
]


@dataclass
class DocumentInfo:
    """Metadata for a doctrine document."""

    path: str
    text: str
    version: str | None
    checksum: str
    last_updated: str


class DocumentRegistry:
    """Collect documents from doctrine directories and expose metadata.

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

    # ------------------------------------------------------------------
    # Internal helpers
    def _extract_version(self, text: str) -> str | None:
        """Return semantic version from document if declared."""
        match = re.search(
            r"^\s*(?:[\-*•]\s*)?Version:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE
        )
        return match.group(1).strip() if match else None

    def _git_last_updated(self, path: Path) -> str:
        """Return ISO timestamp of last commit touching ``path``.

        Falls back to file modification time if git metadata is unavailable.
        """

        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%cI", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            ts = result.stdout.strip()
            if ts:
                return ts
        except Exception:  # pragma: no cover - git may be missing
            pass
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat()

    # ------------------------------------------------------------------
    def iter_documents(self) -> Iterator[DocumentInfo]:
        """Yield :class:`DocumentInfo` for markdown files under ``roots``."""

        for root in self._roots:
            if not root.exists():
                continue
            for path in root.rglob("*.md"):
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:  # pragma: no cover - file may be unreadable
                    continue
                checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
                version = self._extract_version(text)
                last_updated = self._git_last_updated(path)
                yield DocumentInfo(
                    path=str(path),
                    text=text,
                    version=version,
                    checksum=checksum,
                    last_updated=last_updated,
                )

    def get_corpus(self) -> Dict[str, str]:
        """Return mapping of file paths to contents."""
        return {doc.path: doc.text for doc in self.iter_documents()}

    # ------------------------------------------------------------------
    def generate_index(self, output: str | Path) -> None:
        """Write a doctrine index markdown file to ``output``."""

        base = Path(__file__).resolve().parents[2]
        docs = sorted(self.iter_documents(), key=lambda d: d.path)
        lines: List[str] = [
            "# Doctrine Index",
            "",
            "| File | Version | Checksum | Last Updated |",
            "| --- | --- | --- | --- |",
        ]
        for doc in docs:
            rel = Path(doc.path).relative_to(base).as_posix()
            version = doc.version or ""
            lines.append(
                f"| [{rel}]({rel}) | {version} | `{doc.checksum}` | {doc.last_updated} |"
            )
        Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")


__all__ = ["DocumentRegistry", "DocumentInfo"]
