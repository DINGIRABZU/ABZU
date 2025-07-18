"""Analyze Python modules using a placeholder GLM endpoint."""
from __future__ import annotations

import logging
from pathlib import Path
import os
from INANNA_AI.glm_integration import GLMIntegration

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - fallback when requests missing
    requests = None  # type: ignore

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = ROOT / "INANNA_AI"
AUDIT_DIR = ROOT / "audit_logs"
ANALYSIS_FILE = AUDIT_DIR / "code_analysis.txt"


def analyze_code(integration: GLMIntegration | None = None) -> str:
    """Send code base to the GLM endpoint and store the suggestions."""
    integration = integration or GLMIntegration()
    if requests is None:
        raise RuntimeError("requests library is required")

    snippets = []
    if CODE_DIR.exists():
        for path in CODE_DIR.rglob("*.py"):
            try:
                snippets.append(f"# {path}\n{path.read_text(encoding='utf-8')}")
            except Exception:  # pragma: no cover - unreadable file
                logger.warning("Failed to read %s", path)

    data = {"text": "\n".join(snippets)}
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.post(
            integration.endpoint,
            json=data,
            timeout=10,
            headers=integration.headers,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        logger.error("Failed to query %s: %s", integration.endpoint, exc)
        raise
    try:
        analysis = resp.json().get("analysis", "")
    except Exception:  # pragma: no cover - non-json response
        analysis = resp.text

    ANALYSIS_FILE.write_text(analysis, encoding="utf-8")
    logger.info("Wrote code analysis to %s", ANALYSIS_FILE)
    return analysis


if __name__ == "__main__":  # pragma: no cover - manual execution
    print(analyze_code())
