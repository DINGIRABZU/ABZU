from __future__ import annotations

"""Fetch README files from GitHub repositories."""

from pathlib import Path
from typing import List, Dict, Any
import base64
import os
import json
import requests

from .. import corpus_memory
from . import github_metadata
import insight_compiler

try:  # pragma: no cover - optional dependency
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore

from .. import config

_LIST_FILE = Path(__file__).resolve().parents[2] / "learning_sources" / "github_repos.txt"
_API_BASE = "https://api.github.com/repos/"
_INSIGHT_FILE = insight_compiler.INSIGHT_FILE


def load_repo_list(path: Path | None = None) -> List[str]:
    """Return repositories listed in ``path``."""
    if path is None:
        path = _LIST_FILE
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def _headers() -> dict:
    token = config.GITHUB_TOKEN
    if not token:
        token = os.getenv("GITHUB_TOKEN", "")
    if token:
        return {"Authorization": f"token {token}"}
    return {}


def load_insight_keywords(path: Path | None = None) -> Dict[str, Any]:
    """Return insight matrix data mapping patterns to info."""
    if path is None:
        path = _INSIGHT_FILE
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except Exception:
        return {}


def fetch_repo(
    repo: str,
    dest_dir: Path | None = None,
    labels: Dict[str, Any] | None = None,
) -> List[Path]:
    """Download README and recent commits for ``repo``.

    ``labels`` are additional metadata fields written to the JSON file.
    """
    if dest_dir is None:
        dest_dir = config.GITHUB_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    owner_repo = repo.strip()

    # Fetch README
    readme_url = f"{_API_BASE}{owner_repo}/readme"
    r = requests.get(readme_url, headers=_headers(), timeout=10)
    r.raise_for_status()
    data = r.json()
    readme_text = base64.b64decode(data.get("content", "")).decode(
        "utf-8", "ignore"
    )
    readme_path = dest_dir / f"{owner_repo.replace('/', '_')}_README.md"
    readme_path.write_text(readme_text, encoding="utf-8")

    # Fetch recent commit messages
    commit_url = f"{_API_BASE}{owner_repo}/commits"
    r = requests.get(commit_url, headers=_headers(), params={"per_page": 5}, timeout=10)
    r.raise_for_status()
    commits = r.json()
    commit_messages = [c.get("commit", {}).get("message", "") for c in commits]
    commit_text = "\n\n".join(commit_messages)
    commit_path = dest_dir / f"{owner_repo.replace('/', '_')}_COMMITS.txt"
    commit_path.write_text(commit_text, encoding="utf-8")

    # Metadata including stars and last commit date
    meta = github_metadata.fetch_repo_metadata(owner_repo)
    if commits:
        meta["last_commit"] = (
            commits[0].get("commit", {}).get("committer", {}).get("date", "")
        )
    if labels:
        meta.update(labels)
    meta_path = dest_dir / f"{owner_repo.replace('/', '_')}_metadata.json"
    meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

    # Create embeddings and store in corpus DB
    if SentenceTransformer is not None:
        try:
            collection = corpus_memory.create_collection()
        except Exception:
            collection = None
        if collection is not None:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            texts = {
                str(readme_path): readme_text,
                str(commit_path): commit_text,
            }
            corpus_memory.add_embeddings(collection, texts, model)

    return [readme_path, commit_path, meta_path]


def fetch_all(
    path: Path | None = None,
    insight_path: Path | None = None,
) -> List[Path]:
    """Fetch all repositories listed in ``path`` filtered by ``insight_path``."""
    files: List[Path] = []
    keywords = load_insight_keywords(insight_path)
    patterns = [p.lower() for p in keywords]
    for repo in load_repo_list(path):
        match_pat = None
        for pat in patterns:
            if pat in repo.lower():
                match_pat = pat
                break
        if patterns and match_pat is None:
            continue
        labels = {}
        if match_pat:
            info = keywords.get(match_pat, {})
            labels = {
                "ritual_function": "github_scrape",
                "alchemical_math": info.get("action_success_rate", 0.0),
                "emotion_tag": info.get("best_tone", ""),
                "intent_pattern": match_pat,
            }
        try:
            files.extend(fetch_repo(repo, labels=labels or None))
        except Exception:
            continue
    return files

