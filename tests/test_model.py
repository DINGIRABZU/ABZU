"""Tests for model."""

from __future__ import annotations

import importlib.util
import logging
import sys
import types
from pathlib import Path

import pytest

pytest.importorskip("tokenizers")
pytest.importorskip("transformers")

from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.trainers import WordLevelTrainer

from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "inanna_model", ROOT / "INANNA_AI_AGENT" / "model.py"
)
model = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(model)  # type: ignore


def create_dummy_model(dir_path: Path) -> None:
    tok = Tokenizer(WordLevel(unk_token="[UNK]"))
    tok.pre_tokenizer = Whitespace()
    trainer = WordLevelTrainer(special_tokens=["[UNK]"])
    tok.train_from_iterator(["hello world"], trainer=trainer)
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="[UNK]")
    fast.save_pretrained(dir_path)

    config = GPT2Config(
        vocab_size=fast.vocab_size,
        n_positions=8,
        n_embd=8,
        n_layer=1,
        n_head=1,
    )
    model_instance = GPT2LMHeadModel(config)
    model_instance.save_pretrained(dir_path)


def test_load_model_returns_objects(tmp_path):
    create_dummy_model(tmp_path)
    mdl, tok = model.load_model(tmp_path)
    assert mdl is not None
    assert tok is not None


def test_load_model_logs_error_on_missing_weights(tmp_path, caplog):
    create_dummy_model(tmp_path)
    # Remove required files to trigger model loading failure
    for name in ["pytorch_model.bin", "model.safetensors", "config.json"]:
        path = tmp_path / name
        if path.exists():
            path.unlink()
    with caplog.at_level(logging.ERROR):
        with pytest.raises(OSError):
            model.load_model(tmp_path)
    assert "Failed to load model" in caplog.text


def test_load_model_logs_error_on_tokenizer_failure(tmp_path, monkeypatch, caplog):
    create_dummy_model(tmp_path)

    def failing_from_pretrained(model_dir, local_files_only=True):
        raise ValueError("tokenizer missing")

    monkeypatch.setattr(
        model,
        "AutoTokenizer",
        types.SimpleNamespace(from_pretrained=failing_from_pretrained),
    )
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError):
            model.load_model(tmp_path)
    assert "Failed to load tokenizer" in caplog.text


def test_load_model_requires_transformers(monkeypatch, tmp_path):
    """load_model should raise ImportError when transformers is unavailable."""
    monkeypatch.setattr(model, "AutoModelForCausalLM", None)
    monkeypatch.setattr(model, "AutoTokenizer", None)
    with pytest.raises(ImportError):
        model.load_model(tmp_path)
