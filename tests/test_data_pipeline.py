from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def test_run_collects_sources(tmp_path, monkeypatch):
    data_pipeline = importlib.import_module("ml.data_pipeline")

    source_dir = tmp_path / "learning_sources"
    source_dir.mkdir()
    (source_dir / "github_repos.txt").write_text("user/repo\n", encoding="utf-8")
    (source_dir / "gutenberg_books.txt").write_text("Book Title\n", encoding="utf-8")
    monkeypatch.setattr(data_pipeline, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(data_pipeline, "GITHUB_LIST", source_dir / "github_repos.txt")
    monkeypatch.setattr(data_pipeline, "GUTENBERG_LIST", source_dir / "gutenberg_books.txt")

    training_dir = tmp_path / "data" / "training_corpus"
    manifest_path = tmp_path / "data" / "training_manifest.json"
    monkeypatch.setattr(data_pipeline, "TRAINING_DIR", training_dir)
    monkeypatch.setattr(data_pipeline, "MANIFEST_PATH", manifest_path)

    fetched_repo = tmp_path / "repo.txt"
    fetched_repo.write_text("hello", encoding="utf-8")
    fake_gs = types.SimpleNamespace(
        fetch_repo=lambda repo: [fetched_repo],
        config=types.SimpleNamespace(GITHUB_DIR=tmp_path),
    )
    fake_pg_file = tmp_path / "book.txt"
    fake_pg_file.write_text("book", encoding="utf-8")
    fake_pg = types.SimpleNamespace(ingest=lambda q: fake_pg_file, SentenceTransformer=None)
    monkeypatch.setattr(data_pipeline, "gs", fake_gs)
    monkeypatch.setattr(data_pipeline, "pg", fake_pg)

    files = data_pipeline.run(embed=False, update=False)

    assert len(files) == 2
    assert all(p.exists() for p in files)
    assert manifest_path.is_file()


def test_load_list_parses_entries(tmp_path):
    file = tmp_path / "list.txt"
    file.write_text("# comment\nrepo1\n\nrepo2", encoding="utf-8")
    data_pipeline = importlib.import_module("ml.data_pipeline")
    assert data_pipeline._load_list(file) == ["repo1", "repo2"]
