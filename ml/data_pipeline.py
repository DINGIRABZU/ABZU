from __future__ import annotations

"""Download text sources and optionally embed them."""

import argparse
import json
import shutil
from pathlib import Path

from INANNA_AI.learning import github_scraper as gs
from INANNA_AI.learning import project_gutenberg as pg
from INANNA_AI import corpus_memory

_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = _ROOT / "learning_sources"
TRAINING_DIR = _ROOT / "data" / "training_corpus"
MANIFEST_PATH = _ROOT / "data" / "training_manifest.json"

GITHUB_LIST = SOURCE_DIR / "github_repos.txt"
GUTENBERG_LIST = SOURCE_DIR / "gutenberg_books.txt"


def _load_list(path: Path) -> list[str]:
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip() for l in lines if l.strip() and not l.startswith("#")]


def _repo_up_to_date(repo: str, meta_path: Path) -> bool:
    if not meta_path.is_file():
        return False
    try:
        existing = json.loads(meta_path.read_text(encoding="utf-8"))
        latest = gs.github_metadata.fetch_repo_metadata(repo)
        return existing.get("updated") == latest.get("updated")
    except Exception:
        return False


def _copy_to_corpus(path: Path) -> Path:
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    dest = TRAINING_DIR / path.name
    shutil.copy(path, dest)
    return dest


def run(embed: bool = False, update: bool = False) -> list[Path]:
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    for repo in _load_list(GITHUB_LIST):
        meta = gs.config.GITHUB_DIR / f"{repo.replace('/', '_')}_metadata.json"
        if update and not _repo_up_to_date(repo, meta):
            pass
        elif update and meta.is_file():
            continue
        try:
            fetched = gs.fetch_repo(repo)
        except Exception:
            continue
        for fp in fetched:
            if fp.suffix.lower() in {".md", ".txt"}:
                files.append(_copy_to_corpus(fp))

    for query in _load_list(GUTENBERG_LIST):
        dest = TRAINING_DIR / f"{query.replace(' ', '_')}.txt"
        if update and dest.exists():
            continue
        try:
            clean = pg.ingest(query)
        except Exception:
            continue
        files.append(_copy_to_corpus(clean))

    manifest = []
    if MANIFEST_PATH.is_file():
        try:
            manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        except Exception:
            manifest = []
    existing = set(manifest)
    for p in files:
        if str(p) not in existing:
            manifest.append(str(p))
    MANIFEST_PATH.write_text(json.dumps(sorted(manifest), indent=2), encoding="utf-8")

    if embed and files:
        if pg.SentenceTransformer is None:
            raise RuntimeError("sentence-transformers library not installed")
        try:
            collection = corpus_memory.create_collection()
        except Exception:
            collection = None
        if collection is not None:
            model = pg.SentenceTransformer("all-MiniLM-L6-v2")
            texts = {str(p): p.read_text(encoding="utf-8") for p in files}
            corpus_memory.add_embeddings(collection, texts, model)

    return files


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="data_pipeline",
        description="Download learning data",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Embed texts into corpus memory",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Fetch only new or changed sources",
    )
    args = parser.parse_args(argv)
    run(embed=args.embed, update=args.update)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
