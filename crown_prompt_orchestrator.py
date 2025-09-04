"""Lightweight prompt orchestrator for the Crown console.

It detects emotion, logs interactions, and delegates prompts to language
models while applying optional personality layers. The functions here read
and write state to databases and memory logs as part of those duties.
"""

from __future__ import annotations

__version__ = "0.0.1"

import argparse
import asyncio
import hashlib
import json
import logging
import sqlite3
import re
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, Awaitable, cast
import os
import sys

# ---------------------------------------------------------------------------
# Ensure local packages like ``audio`` are importable without installation.
# This mirrors the pytest configuration that adds ``src`` to ``PYTHONPATH``.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_py_path = os.environ.get("PYTHONPATH", "")
if str(_SRC) not in _py_path.split(os.pathsep):
    os.environ["PYTHONPATH"] = os.pathsep.join([p for p in (str(_SRC), _py_path) if p])

import audio  # noqa: F401  # Required for crown_decider audio features

import crown_decider
import emotional_state
import servant_model_manager as smm
from core.memory_physical import PhysicalEvent, store_physical_event
from corpus_memory_logging import load_interactions, log_interaction, log_suggestion
from INANNA_AI import emotion_analysis, emotional_memory
from INANNA_AI.glm_integration import GLMIntegration
from memory.mental import record_task_flow
from memory.sacred import generate_sacred_glyph
from memory.spiritual import map_to_symbol
from spiral_memory import REGISTRY_DB, spiral_recall
from state_transition_engine import StateTransitionEngine
from task_profiling import classify_task

try:
    _settings_mod = import_module("config.settings")
    is_layer_enabled = getattr(_settings_mod, "is_layer_enabled", lambda name: True)
except ImportError:  # pragma: no cover - missing config

    def is_layer_enabled(name: str) -> bool:  # type: ignore
        return True


logger = logging.getLogger(__name__)

_EMOTION_KEYS = list(emotion_analysis.EMOTION_ARCHETYPES.keys())


_STATE_ENGINE = StateTransitionEngine()

TEST_METRICS_FILE = Path("monitoring/pytest_metrics.prom")
_SERVANT_STATE_FILE = Path("data/servant_state.json")


def _is_servant_healthy(name: str) -> bool:
    """Return stored health flag for servant ``name``.

    Absent or unreadable state files default to ``True`` so newly deployed
    servants are considered healthy until proven otherwise.
    """
    try:
        data = json.loads(_SERVANT_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    return bool(data.get("health", {}).get(name, True))


def _detect_emotion(text: str) -> str:
    lowered = text.lower()
    for key in _EMOTION_KEYS:
        if key in lowered:
            return key
    return "neutral"


def _build_context(limit: int = 3) -> str:
    entries = load_interactions(limit=limit)
    if not entries:
        return "<no interactions>"
    parts = [e.get("input", "") for e in entries if e.get("input")]
    return "\n".join(parts)


async def _delegate(prompt: str, glm: GLMIntegration) -> str:
    return await asyncio.to_thread(glm.complete, prompt)


def _apply_layer(message: str) -> tuple[str | None, str | None]:
    """Return layer-transformed text and model name if a layer is active."""
    layer_name = emotional_state.get_current_layer()
    if not layer_name or not is_layer_enabled(layer_name):
        return None, None
    try:
        layers_mod = import_module("INANNA_AI.personality_layers")
    except ImportError:
        return None, None
    registry = getattr(layers_mod, "REGISTRY", {})
    cls = registry.get(layer_name)
    if cls is None:
        return None, None
    try:
        layer = cls()
        if hasattr(layer, "generate_response"):
            return str(layer.generate_response(message)), layer_name
        if hasattr(layer, "speak"):
            return str(layer.speak(message)), layer_name
    except (AttributeError, TypeError):
        logging.exception("layer %s failed", layer_name)
        return None, None
    except Exception:
        logging.exception("unexpected error in layer %s", layer_name)
        raise
    return None, None


def review_test_outcomes(metrics_file: Path = TEST_METRICS_FILE) -> list[str]:
    """Inspect Prometheus metrics and log improvement suggestions.

    Suggestions are logged via :func:`corpus_memory_logging.log_suggestion` and
    returned for inclusion in the orchestrator result.
    """

    if not metrics_file.exists():
        return []
    suggestions: list[str] = []
    try:
        content = metrics_file.read_text(encoding="utf-8")
        match = re.search(r"pytest_test_failures_total\s+(\d+)", content)
        if match and int(match.group(1)) > 0:
            failures = int(match.group(1))
            suggestion = f"Resolve {failures} failing test(s)"
            log_suggestion(suggestion, {"failures": failures})
            suggestions.append(suggestion)
    except (OSError, UnicodeDecodeError, ValueError):  # pragma: no cover - best effort
        logging.exception("test outcome review failed")
    return suggestions


async def crown_prompt_orchestrator_async(
    message: str, glm: GLMIntegration
) -> Dict[str, Any]:
    """Return GLM or servant model reply with metadata."""
    emotion = _detect_emotion(message)
    archetype = emotion_analysis.emotion_to_archetype(emotion)
    weight = emotion_analysis.emotion_weight(emotion)
    state = _STATE_ENGINE.update_state(message)
    context = _build_context()
    prompt_body = f"{context}\n{message}" if context else message
    prompt = f"[{state}]\n{prompt_body}"

    stable_id = hashlib.sha256(message.encode()).hexdigest()

    # ----------------------------------------------- cross-layer integrations
    try:
        store_physical_event(PhysicalEvent("text", message))
    except (OSError, RuntimeError, ValueError):
        logging.exception("physical store failed")
    except Exception:
        logging.exception("unexpected physical store error")
        raise

    try:
        record_task_flow(f"msg_{stable_id}", {"message": message, "emotion": emotion})
    except RuntimeError:
        logging.exception("task flow logging failed")
    except Exception:
        logging.exception("unexpected task flow logging error")
        raise

    symbols = [
        "☉",
        "☾",
        "⚚",
        "♇",
        "♈",
        "♉",
        "♊",
        "♋",
        "♌",
        "♍",
        "♎",
        "♏",
        "♐",
        "♑",
        "♒",
        "♓",
    ]
    symbol_index = int(stable_id, 16) % len(symbols)
    symbol = symbols[symbol_index]
    try:
        map_to_symbol((message, symbol))
    except sqlite3.Error:
        logging.exception("symbol mapping failed")
    except Exception:
        logging.exception("unexpected symbol mapping error")
        raise

    glyph_path: str | None = None
    glyph_phrase: str | None = None
    layers = {
        "physical": [float(len(message))],
        "mental": [float(weight)],
        "emotional": [float(weight)],
        "spiritual": [float(ord(symbol[0]))],
    }
    try:
        path, glyph_phrase = generate_sacred_glyph(layers)
        glyph_path = str(path)
        conn = sqlite3.connect(REGISTRY_DB)
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event TEXT,
                    glyph_path TEXT,
                    phrase TEXT
                )
                """
            )
            conn.execute(
                (
                    "INSERT INTO events (timestamp, event, glyph_path, "
                    "phrase) VALUES (?, ?, ?, ?)"
                ),
                (datetime.utcnow().isoformat(), message, glyph_path, glyph_phrase),
            )
    except (sqlite3.Error, ValueError, OSError):
        logging.exception("glyph generation failed")
    except Exception:
        logging.exception("unexpected glyph generation error")
        raise

    try:
        recall = spiral_recall(message)
    except (sqlite3.Error, OSError):
        logging.exception("spiral recall failed")
        recall = ""
    except Exception:
        logging.exception("unexpected spiral recall error")
        raise

    if glyph_path:
        meta_file = Path(__file__).resolve().parent / "data" / "last_glyph.json"
        try:
            meta_file.parent.mkdir(parents=True, exist_ok=True)
            meta_file.write_text(
                json.dumps({"path": glyph_path, "phrase": glyph_phrase}),
                encoding="utf-8",
            )
        except OSError:
            logging.exception("failed to write glyph metadata")
        except Exception:
            logging.exception("unexpected glyph metadata error")
            raise

    layer_text, layer_model = _apply_layer(message)

    if layer_text is not None:
        text, model = layer_text, layer_model or "layer"
    else:
        current = await emotional_state.get_last_emotion_async()
        logger.debug("processing with last emotion %s", current)
        task_type = classify_task(message)
        if task_type in {"repair", "refactor"}:
            model = "opencode"
        else:
            model = crown_decider.recommend_llm(task_type, emotion)
        success = True
        invoke_error: str | None = None
        if model != "glm" and not _is_servant_healthy(model):
            success = False
            invoke_error = "unhealthy"
            crown_decider.record_result(model, False)
            log_interaction(message, {"emotion": emotion}, {"model": model}, "error")
            logger.warning("servant %s unhealthy; falling back to glm", model)
            model = "glm"
            text = await _delegate(prompt, glm)
            crown_decider.record_result(model, True)
        else:
            try:
                if model == "glm":
                    text = await _delegate(prompt, glm)
                else:
                    text = await smm.invoke(model, message)
            except (KeyError, RuntimeError, OSError, ValueError) as exc:
                success = False
                invoke_error = str(exc)
                crown_decider.record_result(model, False)
                log_interaction(
                    message, {"emotion": emotion}, {"model": model}, "error"
                )
                model = "glm"
                text = await _delegate(prompt, glm)
                crown_decider.record_result(model, True)
            except Exception:
                logging.exception("unexpected model invocation error")
                raise
        affect = emotional_memory.score_affect(text, emotion)
        emotional_memory.record_interaction(
            emotional_memory.EmotionalMemoryNode(
                llm_name=model,
                prompt=message,
                response=text,
                emotion=emotion,
                success=success,
                archetype=archetype,
                affect=affect,
            )
        )
        if success:
            crown_decider.record_result(model, True)

    result = {
        "text": text,
        "model": model,
        "emotion": emotion,
        "archetype": archetype,
        "weight": weight,
        "state": state,
        "context_used": context,
        "symbol": symbol,
        "glyph_path": glyph_path,
        "glyph_phrase": glyph_phrase,
        "spiral_recall": recall,
    }

    if "invoke_error" in locals() and invoke_error is not None:
        result["error"] = invoke_error

    suggestions = review_test_outcomes()
    if suggestions:
        result["suggestions"] = suggestions

    return result


def crown_prompt_orchestrator(
    message: str, glm: GLMIntegration
) -> Dict[str, Any] | Awaitable[Dict[str, Any]]:
    """Synchronously run or return async orchestrator based on event loop."""
    coro = crown_prompt_orchestrator_async(message, glm)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    else:
        return coro


def main(argv: list[str] | None = None) -> None:  # pragma: no cover - CLI entry
    """Run a single orchestrated prompt from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("message", help="Input message to process")
    parser.add_argument("--model", help="Dotted path to model class")
    parser.add_argument("--endpoint", help="Model endpoint URL")
    parser.add_argument("--api-key", help="Model API key")
    parser.add_argument(
        "--temperature", type=float, default=0.8, help="Sampling temperature"
    )
    args = parser.parse_args(argv)

    if args.model:
        mod_name, cls_name = args.model.rsplit(".", 1)
        cls = getattr(import_module(mod_name), cls_name)
    else:
        cls = GLMIntegration

    glm = cls(
        endpoint=args.endpoint,
        api_key=args.api_key,
        temperature=args.temperature,
    )
    result = crown_prompt_orchestrator(args.message, glm)
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    print(cast(Dict[str, Any], result).get("text", ""))


__all__ = ["crown_prompt_orchestrator", "crown_prompt_orchestrator_async", "main"]


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
