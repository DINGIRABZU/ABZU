from __future__ import annotations

"""Fetch metadata for GitHub repositories."""

import json
import os
from pathlib import Path
import requests

from .. import config

_API_BASE = "https://api.github.com/repos/"


def _headers() -> dict:
    token = config.GITHUB_TOKEN or os.getenv("GITHUB_TOKEN", "")
    if token:
        return {"Authorization": f"token {token}"}
    return {}


def fetch_repo_metadata(repo: str) -> dict:
    """Return star count and last update date for ``repo``."""
    url = f"{_API_BASE}{repo}"
    resp = requests.get(url, headers=_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "stars": int(data.get("stargazers_count", 0)),
        "updated": data.get("updated_at", ""),
    }


def build_metadata(mapping: dict[str, list[str]]) -> dict[str, dict[str, dict]]:
    """Fetch metadata for all repositories in ``mapping``."""
    result: dict[str, dict[str, dict]] = {}
    for category, urls in mapping.items():
        repos: dict[str, dict] = {}
        for url in urls:
            if url.startswith("https://github.com/"):
                repo = url[len("https://github.com/") :].rstrip("/")
            elif url.startswith("http://github.com/"):
                repo = url[len("http://github.com/") :].rstrip("/")
            else:
                continue
            try:
                repos[repo] = fetch_repo_metadata(repo)
            except Exception:
                repos[repo] = {}
        result[category] = repos
    return result


def save_metadata(data: dict[str, dict[str, dict]], path: Path) -> None:
    """Save metadata mapping as JSON to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

