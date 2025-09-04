"""Coordinate model and expression routing for the Crown agent.

This module queries orchestrators and recent emotional context to choose an
LLM and expressive parameters. Importing it touches optional vector memory
services when available.
"""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict
import time

import emotional_state
from crown_decider import decide_expression_options
from rag.orchestrator import MoGEOrchestrator

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Gauge, REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Counter = Gauge = REGISTRY = None  # type: ignore[assignment]

_START_TIME = time.perf_counter()

if Gauge is not None and REGISTRY is not None:
    if "service_boot_duration_seconds" in REGISTRY._names_to_collectors:
        BOOT_DURATION_GAUGE = REGISTRY._names_to_collectors["service_boot_duration_seconds"]  # type: ignore[assignment]
    else:
        BOOT_DURATION_GAUGE = Gauge(
            "service_boot_duration_seconds",
            "Duration of service startup in seconds",
            ["service"],
        )
else:
    BOOT_DURATION_GAUGE = None

if Counter is not None and REGISTRY is not None:
    if "narrative_throughput_total" in REGISTRY._names_to_collectors:
        THROUGHPUT_COUNTER = REGISTRY._names_to_collectors["narrative_throughput_total"]  # type: ignore[assignment]
    else:
        THROUGHPUT_COUNTER = Counter(
            "narrative_throughput_total",
            "Narrative events processed",
            ["service"],
        )
    if "service_errors_total" in REGISTRY._names_to_collectors:
        ERROR_COUNTER = REGISTRY._names_to_collectors["service_errors_total"]  # type: ignore[assignment]
    else:
        ERROR_COUNTER = Counter(
            "service_errors_total",
            "Number of errors encountered",
            ["service"],
        )
else:
    THROUGHPUT_COUNTER = ERROR_COUNTER = None

try:  # pragma: no cover - optional dependency
    import vector_memory as _vector_memory
except ImportError:  # pragma: no cover - optional dependency
    _vector_memory = None  # type: ignore[assignment]
vector_memory = _vector_memory
"""Optional vector memory subsystem; ``None`` if unavailable."""

if BOOT_DURATION_GAUGE is not None:
    BOOT_DURATION_GAUGE.labels("crown").set(time.perf_counter() - _START_TIME)


def route_decision(
    text: str,
    emotion_data: Dict[str, Any],
    orchestrator: MoGEOrchestrator | None = None,
) -> Dict[str, Any]:
    """Return combined routing decision for ``text``.

    The function delegates model selection to :class:`MoGEOrchestrator` and
    chooses expression options based on both the current emotion and recent
    history.  Past ``expression_decision`` records are retrieved from
    :mod:`vector_memory` and weighted higher when their stored ``soul_state``
    matches :func:`emotional_state.get_soul_state`.  These weights influence the
    final ``tts_backend`` and ``avatar_style`` choices in addition to the
    baseline recommendation from :func:`crown_decider.decide_expression_options`.

    Parameters
    ----------
    text:
        User input text.
    emotion_data:
        Parsed emotion information for the input.
    orchestrator:
        Optional existing :class:`MoGEOrchestrator` instance.

    Returns
    -------
    Dict[str, Any]
        Decision containing ``model``, ``tts_backend``, ``avatar_style`` and
        ``aura``.
    """
    if THROUGHPUT_COUNTER is not None:
        THROUGHPUT_COUNTER.labels("crown").inc()
    try:
        orch = orchestrator or MoGEOrchestrator()
        result = orch.route(
            text,
            emotion_data,
            text_modality=False,
            voice_modality=False,
            music_modality=False,
        )

        emotion = emotion_data.get("emotion", "neutral")
        opts = decide_expression_options(emotion)

        soul = emotional_state.get_soul_state()
        if vector_memory is not None:
            try:
                records = vector_memory.search(
                    "",
                    filter={"type": "expression_decision", "emotion": emotion},
                    k=20,
                )
            except Exception:
                records = []
        else:
            records = []
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("crown").inc()
        raise

    backend_weights: Dict[str, float] = {opts.get("tts_backend", ""): 1.0}
    avatar_weights: Dict[str, float] = {opts.get("avatar_style", ""): 1.0}
    for rec in records:
        w = 2.0 if soul and rec.get("soul_state") == soul else 1.0
        b = rec.get("tts_backend")
        a = rec.get("avatar_style")
        if b:
            backend_weights[b] = backend_weights.get(b, 0.0) + w
        if a:
            avatar_weights[a] = avatar_weights.get(a, 0.0) + w

    tts_backend = max(backend_weights, key=backend_weights.__getitem__)
    avatar_style = max(avatar_weights, key=avatar_weights.__getitem__)

    return {
        "model": result.get("model"),
        "tts_backend": tts_backend,
        "avatar_style": avatar_style,
        "aura": opts.get("aura"),
    }


__all__ = ["route_decision"]
