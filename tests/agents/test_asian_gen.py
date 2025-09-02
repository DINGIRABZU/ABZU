"""Tests for asian gen."""

from __future__ import annotations

import logging
import pytest
from pathlib import Path

from agents.asian_gen.creative_engine import CreativeEngine


def test_locale_routed_generation(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    class DummyTokenizer:
        lang_code_to_id = {"ja": 7}

    class DummyAutoTokenizer:
        @staticmethod
        def from_pretrained(model_name, local_files_only=True):
            return DummyTokenizer()

    class DummyPipe:
        def __call__(
            self,
            prompt,
            max_new_tokens,
            num_return_sequences,
            forced_bos_token_id=None,
        ):
            assert forced_bos_token_id == 7
            return [{"generated_text": "response"}]

    monkeypatch.setattr(
        "agents.asian_gen.creative_engine.AutoTokenizer", DummyAutoTokenizer
    )
    monkeypatch.setattr(
        "agents.asian_gen.creative_engine.pipeline", lambda *a, **k: DummyPipe()
    )

    engine = CreativeEngine()
    text = engine.generate("hello", locale="ja")
    assert text == "response"
    assert "Loaded AutoTokenizer" in caplog.text
    assert "Built transformers generator" in caplog.text


def test_sentencepiece_fallback(monkeypatch, caplog, tmp_path):
    monkeypatch.setattr("agents.asian_gen.creative_engine.AutoTokenizer", None)
    monkeypatch.setattr("agents.asian_gen.creative_engine.pipeline", None)

    class DummySP:
        class SentencePieceProcessor:
            def load(self, path):
                pass

            def encode(self, text, out_type=str):
                return ["tok"]

        class SentencePieceTrainer:
            @staticmethod
            def train(input, model_prefix, **kwargs):
                Path(model_prefix + ".model").touch()

    monkeypatch.setattr("agents.asian_gen.creative_engine.spm", DummySP)
    caplog.set_level(logging.INFO)

    engine = CreativeEngine()

    output = engine.generate("hello", locale="ja")
    assert isinstance(output, str) and output
    assert "Using SentencePiece fallback" in caplog.text
    assert "Transformers pipeline not available" in caplog.text


def test_sentencepiece_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("agents.asian_gen.creative_engine.spm", None)
    monkeypatch.setattr("agents.asian_gen.creative_engine.AutoTokenizer", None)
    engine = CreativeEngine.__new__(CreativeEngine)
    engine.spm_path = str(tmp_path / "spm.model")
    with pytest.raises(RuntimeError, match="sentencepiece not installed"):
        engine._load_tokenizer()
