from __future__ import annotations

"""Model selection and benchmarking utilities."""

from pathlib import Path
from typing import Dict, List

from INANNA_AI import db_storage

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]
vector_memory = _vector_memory
"""Optional vector memory subsystem; ``None`` if unavailable."""

# Emotion to model lookup derived from docs/crown_manifest.md
_EMOTION_MODEL_MATRIX = {
    "joy": "deepseek",
    "excited": "deepseek",
    "stress": "mistral",
    "fear": "mistral",
    "sad": "mistral",
    "calm": "glm",
    "neutral": "glm",
}


class ModelSelector:
    """Pick the best language model and update routing weights."""

    def __init__(self, *, db_path: Path | None = None, alpha: float = 0.1) -> None:
        self.db_path = db_path or db_storage.DB_PATH
        db_storage.init_db(self.db_path)
        self._alpha = alpha
        self.model_weights: Dict[str, float] = {
            "glm": 1.0,
            "deepseek": 1.0,
            "mistral": 1.0,
        }

    @staticmethod
    def model_from_emotion(emotion: str) -> str:
        return _EMOTION_MODEL_MATRIX.get(emotion.lower(), "glm")

    @staticmethod
    def _coherence(text: str) -> float:
        words = text.split()
        if not words:
            return 0.0
        return len(set(words)) / len(words)

    @staticmethod
    def _relevance(source: str, generated: str) -> float:
        src = set(source.split())
        gen = set(generated.split())
        if not src or not gen:
            return 0.0
        return len(src & gen) / len(src | gen)

    def _update_weights(self, model: str, rt: float, coh: float, rel: float) -> None:
        reward = coh + rel - 0.1 * rt
        current = self.model_weights.get(model, 1.0)
        self.model_weights[model] = (1 - self._alpha) * current + self._alpha * reward

    def choose(
        self,
        task: str,
        weight: float,
        history: List[str],
        *,
        weights: Dict[str, float] | None = None,
    ) -> str:
        emotional_ratio = 0.0
        if history:
            emotional_ratio = history.count("emotional") / len(history)

        base = {"glm": 0.0, "deepseek": 0.0, "mistral": 0.0}

        if weight > 0.8 or emotional_ratio > 0.5 or task == "philosophical":
            base["mistral"] = 1.0
        if task == "instructional":
            base["deepseek"] = 1.0
        if not any(base.values()):
            base["glm"] = 1.0

        effective = weights or self.model_weights
        scores = {m: base[m] * effective.get(m, 1.0) for m in base}
        return max(scores, key=scores.get)

    def benchmark(self, model: str, prompt: str, output: str, elapsed: float) -> None:
        coh = self._coherence(output)
        rel = self._relevance(prompt, output)
        db_storage.log_benchmark(model, elapsed, coh, rel, db_path=self.db_path)
        self._update_weights(model, elapsed, coh, rel)

    def select_model(
        self,
        task: str,
        emotion: str,
        weight: float,
        history: List[str],
    ) -> str:
        """Return the model best suited for the given context."""
        if vector_memory is not None:
            try:
                records = vector_memory.query_vectors(
                    filter={"type": "routing_decision", "emotion": emotion},
                    limit=10,
                )
            except Exception:
                records = []
        else:
            records = []

        mem_weights = dict(self.model_weights)
        for rec in records:
            m = rec.get("selected_model")
            if m in mem_weights:
                mem_weights[m] += 0.1

        emotion_model = self.model_from_emotion(emotion)
        mem_weights[emotion_model] = mem_weights.get(emotion_model, 1.0) + 0.2

        candidate = self.choose(task, weight, history, weights=mem_weights)
        if mem_weights.get(candidate, 0.0) > mem_weights.get(emotion_model, 0.0):
            return candidate
        return emotion_model
