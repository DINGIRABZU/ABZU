"""Lightweight transformer stubs for testing."""

from __future__ import annotations

__version__ = "0.1.0"

import json
from pathlib import Path


class GenerationMixin:
    """Minimal text generation utilities."""

    def generate(self, max_length: int = 1, **kwargs):
        """Return a sequence of token ids filled with zeros.

        Parameters
        ----------
        max_length:
            Length of the generated sequence.
        kwargs:
            Unused additional parameters for API compatibility.
        """

        return [[0] * max_length]


class GPT2Config:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)

    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path) / "config.json").write_text(json.dumps(self.to_dict()))

    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        data = json.loads((Path(path) / "config.json").read_text())
        return cls(**data)


class GPT2LMHeadModel(GenerationMixin):
    def __init__(self, config):
        self.config = config

    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        cfg = GPT2Config.from_pretrained(path)
        return cls(cfg)

    @classmethod
    def from_config(cls, config):
        return cls(config)

    def save_pretrained(self, path):
        self.config.save_pretrained(path)


class AutoConfig:
    from_pretrained = GPT2Config.from_pretrained


class AutoModelForCausalLM:
    from_pretrained = GPT2LMHeadModel.from_pretrained
    from_config = GPT2LMHeadModel.from_config


class PreTrainedTokenizerFast:
    def __init__(self, tokenizer_object=None, unk_token="[UNK]"):
        self.tokenizer_object = tokenizer_object
        self.unk_token = unk_token
        self.vocab_size = len(tokenizer_object.get_vocab()) if tokenizer_object else 0

    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        (Path(path) / "tokenizer.json").write_text("{}")


class AutoTokenizer:
    @classmethod
    def from_pretrained(cls, path, *args, **kwargs):
        return PreTrainedTokenizerFast()


__all__ = [
    "GenerationMixin",
    "GPT2Config",
    "GPT2LMHeadModel",
    "PreTrainedTokenizerFast",
    "AutoConfig",
    "AutoModelForCausalLM",
    "AutoTokenizer",
]
