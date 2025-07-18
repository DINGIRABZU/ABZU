"""Generate a short self-description using a placeholder GLM endpoint."""
from __future__ import annotations

import logging
from pathlib import Path
import os

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - fallback when requests missing
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
INANNA_DIR = ROOT / "INANNA_AI"
QNL_DIR = ROOT / "QNL_LANGUAGE"
AUDIT_DIR = ROOT / "audit_logs"
INSIGHTS_FILE = AUDIT_DIR / "existential_insights.txt"
ENDPOINT = os.getenv("GLM_API_URL", "https://api.example.com/glm")
API_KEY = os.getenv("GLM_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else None

from . import emotion_analysis, context, adaptive_learning


class ExistentialReflector:
    """Helper to query the GLM about the system identity."""

    wording_choices: list[str] = ["I am"]

    @staticmethod
    def reflect_on_identity() -> str:
        """Return a concise self-description derived from project texts."""
        if requests is None:
            raise RuntimeError("requests library is required")

        texts = []
        for directory in (INANNA_DIR, QNL_DIR):
            if directory.exists():
                for path in directory.glob("*.md"):
                    try:
                        texts.append(path.read_text(encoding="utf-8"))
                    except Exception:  # pragma: no cover - unreadable file
                        logger.warning("Failed to read %s", path)

        data = {"text": "\n".join(texts)}
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            resp = requests.post(ENDPOINT, json=data, timeout=10, headers=HEADERS)
            resp.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            logger.error("Failed to query %s: %s", ENDPOINT, exc)
            raise

        try:
            desc = resp.json().get("description", "")
        except Exception:  # pragma: no cover - non-json response
            desc = resp.text

        INSIGHTS_FILE.write_text(desc, encoding="utf-8")
        logger.info("Wrote existential insights to %s", INSIGHTS_FILE)
        return desc

    @staticmethod
    def reflect_on_dilemma(prompt: str, emotion: str) -> str:
        """Return a short reflection on ``prompt`` using recent context."""
        if requests is None:
            raise RuntimeError("requests library is required")

        context.add(prompt)
        recent_ctx = context.recent()
        payload = {
            "prompt": prompt,
            "emotion": emotion,
            "archetype": emotion_analysis.emotion_to_archetype(emotion),
            "context": recent_ctx,
        }

        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        try:
            resp = requests.post(ENDPOINT, json=payload, timeout=10, headers=HEADERS)
            resp.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            logger.error("Failed to query %s: %s", ENDPOINT, exc)
            raise

        try:
            reflection = resp.json().get("description", "")
        except Exception:  # pragma: no cover - non-json response
            reflection = resp.text

        INSIGHTS_FILE.write_text(reflection, encoding="utf-8")
        logger.info("Wrote existential insights to %s", INSIGHTS_FILE)
        return reflection

    @classmethod
    def apply_feedback(
        cls,
        reward: float,
        wording: list[str] | None = None,
    ) -> None:
        """Update learning agent with reflector feedback."""
        adaptive_learning.update(
            reflector_reward=reward,
            reflector_wording=wording,
        )
        if wording:
            cls.wording_choices = wording


if __name__ == "__main__":  # pragma: no cover - manual execution
    print(ExistentialReflector.reflect_on_identity())
