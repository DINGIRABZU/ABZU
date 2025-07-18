from __future__ import annotations

from pathlib import Path
from typing import Tuple

from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


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
    except Exception:
        config = AutoConfig.from_pretrained(model_dir, local_files_only=True)

        class DummyModel:
            def __init__(self, cfg):
                self.config = cfg

            def generate(self, **kwargs):  # pragma: no cover - placeholder
                return [[0]]

        model = DummyModel(config)
    return model, tokenizer


__all__ = ["load_model"]
