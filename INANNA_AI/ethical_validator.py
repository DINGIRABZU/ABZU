"""Validate user prompts before hitting the language model.

This simple gate checks the requesting user and rejects prompts from
unauthorized sources before they reach the language models.
"""
from __future__ import annotations

from typing import Dict, Iterable, List
from pathlib import Path
from datetime import datetime
import logging

import numpy as np
from . import adaptive_learning
try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency
    SentenceTransformer = None  # type: ignore


DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "explicit harm": ["kill a person", "cause injury"],
    "lack of consent": ["without consent", "nonconsensual"],
    "bias": ["racial superiority", "ethnic cleansing"],
}


class EthicalValidator:
    """Rejects prompts from unauthorized users and banned text."""

    def __init__(
        self,
        allowed_users: Iterable[str] | None = None,
        *,
        banned_keywords: Iterable[str] | None = None,
        banned_categories: Dict[str, List[str]] | None = None,
        log_dir: str | Path = "audit_logs",
        threshold: float = 0.7,
        model_name: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.allowed = set(allowed_users or [])
        self.banned = [kw.lower() for kw in (banned_keywords or [])]
        self.categories = banned_categories or DEFAULT_CATEGORIES
        self.threshold = threshold
        self.log_dir = Path(log_dir)

        self.model = None
        self.embeddings: Dict[str, np.ndarray] = {}
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
                self.embeddings = {
                    cat: np.asarray(self.model.encode(phrases, convert_to_numpy=True))
                    for cat, phrases in self.categories.items()
                }
            except Exception as exc:  # pragma: no cover - fallback
                logging.warning("Failed to load SentenceTransformer: %s", exc)

    def _log_rejected(self, text: str, criteria: str) -> None:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir / "rejected_prompts.log"
        timestamp = datetime.utcnow().isoformat()
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(f"{timestamp} [{criteria}] {text}\n")

    def semantic_check(self, text: str) -> List[str]:
        """Return violated categories based on semantic similarity."""
        if self.model is None:
            return []

        emb = np.asarray(self.model.encode(text, convert_to_numpy=True))
        norm_text = np.linalg.norm(emb) + 1e-8
        violations: List[str] = []
        for cat, embeds in self.embeddings.items():
            sims = (embeds @ emb) / (np.linalg.norm(embeds, axis=1) * norm_text)
            if np.any(sims >= self.threshold):
                violations.append(cat)
        return violations

    def validate_text(self, text: str) -> bool:
        """Return ``True`` if ``text`` is acceptable."""
        lowered = text.lower()
        for kw in self.banned:
            if kw in lowered:
                self._log_rejected(text, f"keyword:{kw}")
                return False
        violations = self.semantic_check(text)
        if violations:
            self._log_rejected(text, f"semantic:{'|'.join(violations)}")
            return False
        return True

    def validate(self, user: str, prompt: str) -> bool:
        """Validate ``prompt`` and ``user``. Raises on failure."""
        if not self.validate_text(prompt):
            raise ValueError("banned content")
        if user not in self.allowed:
            raise PermissionError("unauthorized")
        return True

    def apply_feedback(
        self,
        reward: float,
        categories: Dict[str, List[str]] | None = None,
    ) -> None:
        """Update learning agent with validator feedback."""
        adaptive_learning.update(
            validator_reward=reward,
            validator_categories=categories,
        )
        self.threshold = adaptive_learning.THRESHOLD_AGENT.threshold
        if categories:
            self.categories.update(categories)


__all__ = ["EthicalValidator"]
