"""Helpers for loading local language models and tokenizers.

The utilities operate solely on files already present on disk and log failures
when the model cannot be instantiated.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)


def load_model(model_dir: str | Path) -> Tuple[object, AutoTokenizer]:
    """Load a local causal language model and tokenizer.

    Parameters
    ----------
    model_dir : str | Path
        Directory containing the model weights and tokenizer files.

    Returns
    -------
    Tuple[AutoModelForCausalLM, AutoTokenizer]
        The loaded model and tokenizer.
    """
    model_dir = Path(model_dir)
    tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    try:
        model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True)
    except (OSError, ValueError) as exc:
        logger.error("Failed to load model from %s: %s", model_dir, exc)
        raise
    return model, tokenizer


__all__ = ["load_model"]
