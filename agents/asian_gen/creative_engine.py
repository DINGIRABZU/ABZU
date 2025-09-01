"""Creative engine for Asian language text generation.

This module tries to load a multilingual Hugging Face model to generate text for
specific locale codes. When the transformers tokenizer or model is not
available, it falls back to a local SentencePiece tokenizer so that basic
operations still function offline.
"""

from __future__ import annotations

__version__ = "0.1.0"

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import tempfile
import logging
import os

try:  # pragma: no cover - optional dependency
    import sentencepiece as spm
except Exception:  # pragma: no cover
    spm = None

try:  # pragma: no cover - optional dependency
    from transformers import AutoTokenizer, pipeline
except Exception:  # pragma: no cover
    AutoTokenizer = None  # type: ignore
    pipeline = None  # type: ignore

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass
class CreativeEngine:
    """Generate short creative text for a given locale."""

    model_name: str = "facebook/mbart-large-50-many-to-many-mmt"
    spm_path: Optional[str] = None
    log_level: Optional[Union[int, str]] = None

    def __post_init__(self) -> None:
        level: Union[int, str, None] = self.log_level or os.getenv(
            "CREATIVE_ENGINE_LOG_LEVEL"
        )
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level if isinstance(level, int) else logging.INFO)
        try:
            self.tokenizer = self._load_tokenizer()
        except RuntimeError:
            self.spm_path = self._ensure_sentencepiece_model()
            self.tokenizer = self._load_tokenizer()
        self.generator = self._build_generator()

    def _load_tokenizer(self):
        if AutoTokenizer is not None:
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name, local_files_only=True
                )
                logger.info("Loaded AutoTokenizer")
                return tokenizer
            except Exception:
                logger.info("AutoTokenizer unavailable; falling back")
        if self.spm_path:
            if spm is None:
                raise RuntimeError("sentencepiece not installed")
            sp = spm.SentencePieceProcessor()
            sp.load(self.spm_path)
            logger.info("Using SentencePiece fallback")
            return sp
        logger.error("No tokenizer available")
        raise RuntimeError("No tokenizer available")

    def _ensure_sentencepiece_model(self) -> str:
        """Train and cache a tiny SentencePiece model."""
        corpus = Path(__file__).with_name("data") / "corpus.txt"
        cache_dir = Path(tempfile.gettempdir()) / "asian_gen_spm"
        model_file = cache_dir / "spm.model"
        if not model_file.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)
            spm.SentencePieceTrainer.train(
                input=str(corpus),
                model_prefix=str(cache_dir / "spm"),
                vocab_size=64,
                model_type="unigram",
                character_coverage=1.0,
            )
        return str(model_file)

    def _build_generator(self):
        if pipeline is None:
            logger.info("Transformers pipeline not available")
            return None
        try:
            gen = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=-1,
                model_kwargs={"local_files_only": True},
            )
            logger.info("Built transformers generator")
            return gen
        except Exception:
            logger.warning("Failed to initialize transformers generator")
            return None

    def generate(self, prompt: str, locale: str) -> str:
        """Generate text conditioned on locale."""

        if self.generator is not None:
            kwargs = {}
            if hasattr(self.tokenizer, "lang_code_to_id"):
                lang_id = self.tokenizer.lang_code_to_id.get(locale)
                if lang_id is not None:
                    kwargs["forced_bos_token_id"] = lang_id
            result = self.generator(
                prompt, max_new_tokens=20, num_return_sequences=1, **kwargs
            )
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "")
            return ""

        if isinstance(self.tokenizer, spm.SentencePieceProcessor):
            tokens = self.tokenizer.encode(prompt, out_type=str)
            return " ".join(tokens)
        return prompt
