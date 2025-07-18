from __future__ import annotations

"""Parse the categorized INANNA training guide."""

from pathlib import Path
import re

_URL_RE = re.compile(r"https?://[^\s)]+")


def parse_training_guide(path: Path) -> dict[str, list[str]]:
    """Return mapping of category to GitHub URLs from ``path``.

    Duplicate URLs across all categories are ignored. Trailing fragments like
    ``#readme`` are removed.
    """
    mapping: dict[str, list[str]] = {}
    current: str | None = None
    seen: set[str] = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            current = stripped[3:].strip()
            mapping.setdefault(current, [])
            continue
        if not current:
            continue
        for match in _URL_RE.findall(stripped):
            url = re.sub(r"#.*$", "", match).rstrip("/")
            if url not in seen:
                mapping[current].append(url)
                seen.add(url)
    return mapping


def write_repo_list(mapping: dict[str, list[str]], dest: Path) -> None:
    """Write unique ``owner/repo`` names from ``mapping`` to ``dest``."""
    repos: list[str] = []
    seen: set[str] = set()
    for urls in mapping.values():
        for url in urls:
            if url.startswith("https://github.com/"):
                repo = url[len("https://github.com/") :].rstrip("/")
            elif url.startswith("http://github.com/"):
                repo = url[len("http://github.com/") :].rstrip("/")
            else:
                continue
            if repo not in seen:
                repos.append(repo)
                seen.add(repo)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(repos), encoding="utf-8")
