"""Tests for preprocess."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import preprocess, source_loader


def test_preprocess_creates_cache(tmp_path):
    text_dir = tmp_path / "INANNA_AI"
    text_dir.mkdir()
    (text_dir / "sample.md").write_text(
        "## Header\n\nThis is **bold** text.", encoding="utf-8"
    )

    config = tmp_path / "source_paths.json"
    config.write_text(json.dumps({"source_paths": [str(text_dir)]}), encoding="utf-8")

    texts = source_loader.load_sources(config)
    cache_dir = tmp_path / "cache"
    tokens = preprocess.preprocess_texts(texts, cache_dir)

    assert tokens == {"sample.md": ["header", "this", "is", "bold", "text"]}
    cache_file = cache_dir / "sample.md.tokens.json"
    assert cache_file.exists()

    # Call again to ensure cache is loaded
    tokens2 = preprocess.preprocess_texts(texts, cache_dir)
    assert tokens2 == tokens


def test_generate_embeddings_creates_npy(tmp_path, monkeypatch):
    tokens = {"sample": ["hello", "world"]}

    class DummyModel:
        def __init__(self, name: str) -> None:
            self.calls = []

        def encode(self, text: str):
            self.calls.append(text)
            return np.array([len(text)])

    monkeypatch.setattr(
        preprocess, "SentenceTransformer", lambda name: DummyModel(name)
    )

    cache_dir = tmp_path / "cache"
    embeds = preprocess.generate_embeddings(
        tokens, cache_dir=cache_dir, model_name="dummy"
    )

    assert (cache_dir / "sample.embed.npy").exists()
    assert embeds["sample"].shape == (1,)

    # Call again to ensure cache is used
    embeds2 = preprocess.generate_embeddings(
        tokens, cache_dir=cache_dir, model_name="dummy"
    )
    assert embeds2["sample"].tolist() == embeds["sample"].tolist()


def test_preprocess_warns_on_bad_cache(tmp_path, caplog):
    text_dir = tmp_path / "INANNA_AI"
    text_dir.mkdir()
    (text_dir / "sample.md").write_text("Hello world", encoding="utf-8")
    config = tmp_path / "source_paths.json"
    config.write_text(json.dumps({"source_paths": [str(text_dir)]}), encoding="utf-8")
    texts = source_loader.load_sources(config)
    cache_dir = tmp_path / "cache"
    preprocess.preprocess_texts(texts, cache_dir)
    cache_file = cache_dir / "sample.md.tokens.json"
    cache_file.write_text("corrupted", encoding="utf-8")
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            preprocess.preprocess_texts(texts, cache_dir)
    assert "Failed to read token cache" in caplog.text


def test_generate_embeddings_warns_on_bad_cache(tmp_path, monkeypatch, caplog):
    tokens = {"sample": ["hello", "world"]}

    class DummyModel:
        def __init__(self, name: str) -> None:
            self.calls = []

        def encode(self, text: str):
            self.calls.append(text)
            return np.array([len(text)])

    monkeypatch.setattr(
        preprocess, "SentenceTransformer", lambda name: DummyModel(name)
    )

    cache_dir = tmp_path / "cache"
    preprocess.generate_embeddings(tokens, cache_dir=cache_dir, model_name="dummy")
    cache_file = cache_dir / "sample.embed.npy"
    cache_file.write_text("corrupted", encoding="utf-8")
    with caplog.at_level("ERROR"):
        with pytest.raises(Exception):
            preprocess.generate_embeddings(
                tokens, cache_dir=cache_dir, model_name="dummy"
            )
    assert "Failed to read embedding cache" in caplog.text
