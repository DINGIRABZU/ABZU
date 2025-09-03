"""Thin wrapper around the real Hugging Face `transformers` package."""

from __future__ import annotations

__version__ = "0.1.0"

import importlib
import sys
from pathlib import Path

# Temporarily remove the repository root so we can import the actual
# `transformers` package installed in the environment rather than this wrapper.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_orig_sys_path = list(sys.path)
sys.modules.pop("transformers", None)
try:  # pragma: no cover - import guard
    sys.path = [p for p in sys.path if Path(p).resolve() != _REPO_ROOT]
    hf = importlib.import_module("transformers")
finally:
    sys.path = _orig_sys_path

_BASE_GPT2 = hf.GPT2LMHeadModel


class GPT2LMHeadModel(_BASE_GPT2):
    """GPT-2 model thin wrapper."""

    @classmethod
    def from_pretrained(
        cls, pretrained_model_name_or_path: str = "distilgpt2", **kwargs
    ):
        model = _BASE_GPT2.from_pretrained(pretrained_model_name_or_path, **kwargs)
        model.__class__ = cls
        return model


# Expose selected utilities from the real library
GenerationMixin = hf.GenerationMixin
AutoConfig = hf.AutoConfig
AutoModelForCausalLM = hf.AutoModelForCausalLM
AutoTokenizer = hf.AutoTokenizer
GPT2Config = hf.GPT2Config
PreTrainedTokenizerFast = hf.PreTrainedTokenizerFast
hf.GPT2LMHeadModel = GPT2LMHeadModel

__all__ = [
    "GenerationMixin",
    "GPT2Config",
    "GPT2LMHeadModel",
    "PreTrainedTokenizerFast",
    "AutoConfig",
    "AutoModelForCausalLM",
    "AutoTokenizer",
]
