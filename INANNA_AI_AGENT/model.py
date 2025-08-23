"""Load local language models and tokenizers.

These helpers operate solely on files already present on disk and log failures
when a model or tokenizer cannot be instantiated.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

try:  # pragma: no cover - import guarded for optional dependency
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError as exc:  # pragma: no cover - handled at runtime
    AutoModelForCausalLM = AutoTokenizer = None  # type: ignore[assignment]
    _TRANSFORMERS_IMPORT_ERROR = exc
else:  # pragma: no cover - simple assignment
    _TRANSFORMERS_IMPORT_ERROR = None

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
    if AutoModelForCausalLM is None or AutoTokenizer is None:
        raise ImportError(
            "The 'transformers' library is required to load models."
        ) from _TRANSFORMERS_IMPORT_ERROR

    model_dir = Path(model_dir)
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
    except (OSError, ValueError) as exc:
        logger.error(
            "Failed to load tokenizer from %s: %s", model_dir, exc, exc_info=exc
        )
        raise
    try:
        model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True)
    except (OSError, ValueError) as exc:
        logger.error("Failed to load model from %s: %s", model_dir, exc, exc_info=exc)
        raise
    return model, tokenizer


__all__ = ["load_model"]
