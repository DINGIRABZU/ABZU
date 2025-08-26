"""Creative engine for Asian language text generation.

This module tries to load a multilingual Hugging Face model to generate text for
specific locale codes. When the transformers tokenizer or model is not
available, it falls back to a local SentencePiece tokenizer so that basic
operations still function offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tempfile

import sentencepiece as spm

try:  # pragma: no cover - optional dependency
    from transformers import AutoTokenizer, pipeline
except Exception:  # pragma: no cover
    AutoTokenizer = None  # type: ignore
    pipeline = None  # type: ignore


@dataclass
class CreativeEngine:
    """Generate short creative text for a given locale."""

    model_name: str = "facebook/mbart-large-50-many-to-many-mmt"
    spm_path: Optional[str] = None

    def __post_init__(self) -> None:
        try:
            self.tokenizer = self._load_tokenizer()
        except RuntimeError:
            self.spm_path = self._ensure_sentencepiece_model()
            self.tokenizer = self._load_tokenizer()
        self.generator = self._build_generator()

    def _load_tokenizer(self):
        if AutoTokenizer is not None:
            try:
                return AutoTokenizer.from_pretrained(
                    self.model_name, local_files_only=True
                )
            except Exception:
                pass
        if self.spm_path:
            sp = spm.SentencePieceProcessor()
            sp.load(self.spm_path)
            return sp
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
            return None
        try:
            return pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=-1,
                model_kwargs={"local_files_only": True},
            )
        except Exception:
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
