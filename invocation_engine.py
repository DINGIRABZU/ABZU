"""Pattern-based invocation engine."""

from __future__ import annotations

import json
import logging
import time
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple

try:  # pragma: no cover - optional dependency
    from prometheus_client import Histogram
except ImportError:  # pragma: no cover - optional dependency
    Histogram = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]
vector_memory = _vector_memory
"""Optional vector memory subsystem; ``None`` if unavailable."""

if TYPE_CHECKING:  # pragma: no cover - avoid circular import at runtime
    from neoabzu_rag import MoGEOrchestrator


logger = logging.getLogger(__name__)
_RITUAL_FILE = Path(__file__).resolve().parent / "ritual_profile.json"

# Map of (symbols, emotion) -> callback
_CALLBACKS: Dict[
    Tuple[str, str | None], Callable[[str, str | None, MoGEOrchestrator | None], Any]
] = {}
# Map of (symbols, emotion) -> orchestrator hook name
_HOOKS: Dict[Tuple[str, str | None], str] = {}

_SYMBOL_RE = re.compile(r"[^\w\s\[\]#]+")
_EMO_RE = re.compile(r"\[(\w+)\]|#(\w+)")

INVOKE_LATENCY = (
    Histogram("invocation_duration_seconds", "Time spent in invoke()")
    if Histogram is not None
    else None
)
RITUAL_LATENCY = (
    Histogram(
        "ritual_invocation_duration_seconds",
        "Time spent in invoke_ritual()",
    )
    if Histogram is not None
    else None
)


def register_invocation(
    symbols: str,
    emotion: str | None = None,
    callback: Callable[[str, str | None, MoGEOrchestrator | None], Any] | None = None,
    *,
    hook: str | None = None,
) -> None:
    """Register an invocation pattern with ``callback`` or orchestrator ``hook``."""
    if callback is None and hook is None:
        raise ValueError("callback or hook required")
    key = (symbols, emotion)
    if callback:
        _CALLBACKS[key] = callback
    if hook:
        _HOOKS[key] = hook
    try:
        vector_memory.add_vector(
            symbols, {"symbols": symbols, "emotion": emotion or ""}
        )
    except AttributeError as exc:
        logger.warning(
            "vector memory unavailable",
            extra={"symbols": symbols, "emotion": emotion},
            exc_info=exc,
        )
    except Exception as exc:
        logger.warning(
            "vector_memory.add_vector failed",
            extra={"symbols": symbols, "emotion": emotion},
            exc_info=exc,
        )


def clear_registry() -> None:
    """Remove all registered invocation patterns."""
    _CALLBACKS.clear()
    _HOOKS.clear()


def _extract_symbols(text: str) -> str:
    parts = _SYMBOL_RE.findall(text)
    return "".join(parts)


def _extract_emotion(text: str) -> str | None:
    m = _EMO_RE.search(text)
    if m:
        return (m.group(1) or m.group(2)).lower()
    return None


def invoke(text: str, orchestrator: MoGEOrchestrator | None = None) -> List[Any]:
    """Process ``text`` and trigger callbacks for matching invocations."""
    start = time.perf_counter()
    symbols = _extract_symbols(text)
    emotion = _extract_emotion(text)
    key = (symbols, emotion)
    results: List[Any] = []

    cb = _CALLBACKS.get(key)
    hk = _HOOKS.get(key)

    if cb is None and hk is None:
        try:
            search_res = vector_memory.search(
                symbols or text, filter={"emotion": emotion} if emotion else None, k=1
            )
        except AttributeError as exc:
            logger.warning(
                "vector memory unavailable",
                extra={"symbols": symbols, "emotion": emotion},
                exc_info=exc,
            )
            search_res = []
        except Exception as exc:
            logger.warning(
                "vector_memory.search failed",
                extra={"symbols": symbols, "emotion": emotion},
                exc_info=exc,
            )
            search_res = []
        if search_res:
            meta = search_res[0]
            key = (
                str(meta.get("symbols", meta.get("text", ""))),
                meta.get("emotion") or None,
            )
            cb = _CALLBACKS.get(key)
            hk = _HOOKS.get(key)

    if cb:
        results.append(cb(symbols, emotion, orchestrator))
    if hk and orchestrator is not None:
        method = getattr(orchestrator, hk, None)
        if callable(method):
            results.append(method(symbols, emotion))
    duration = time.perf_counter() - start
    if INVOKE_LATENCY is not None:
        INVOKE_LATENCY.observe(duration)
    logger.info(
        "invoke completed",
        extra={"symbols": symbols, "emotion": emotion, "duration": duration},
    )
    return results


def invoke_ritual(name: str) -> List[str]:
    """Return ritual steps for ``name`` and log the invocation."""
    start = time.perf_counter()
    try:
        data = json.loads(_RITUAL_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        duration = time.perf_counter() - start
        logger.error(
            "failed to load %s",
            _RITUAL_FILE,
            extra={"duration": duration},
            exc_info=exc,
        )
        return []
    info = data.get(name)
    steps: List[str] = []
    if isinstance(info, list):
        steps.extend(str(a) for a in info)
    elif isinstance(info, dict):
        for actions in info.values():
            if isinstance(actions, list):
                steps.extend(str(a) for a in actions)
    else:
        info = {}
    duration = time.perf_counter() - start
    if RITUAL_LATENCY is not None:
        RITUAL_LATENCY.observe(duration)
    logger.info("ritual invoked", extra={"ritual": name, "duration": duration})
    return steps


__all__ = ["register_invocation", "invoke", "clear_registry", "invoke_ritual"]
