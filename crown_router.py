"""Coordinate model and expression routing for the Crown agent.

This module queries orchestrators and recent emotional context to choose an
LLM and expressive parameters. Importing it touches optional vector memory
services when available.
"""

from __future__ import annotations

__version__ = "0.1.0"

from typing import Any, Dict
import time
import os
import json
import asyncio

import emotional_state
from crown_decider import decide_expression_options
from rag.orchestrator import MoGEOrchestrator
from INANNA_AI.ethical_validator import EthicalValidator
from agents.nazarick.document_registry import DocumentRegistry

try:  # pragma: no cover - optional dependency
    from monitoring.chakra_heartbeat import ChakraHeartbeat

    heartbeat_monitor = ChakraHeartbeat()
except Exception:  # pragma: no cover - heartbeat optional
    heartbeat_monitor = None

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Gauge, Histogram, REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Counter = Gauge = Histogram = REGISTRY = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import pynvml

    pynvml.nvmlInit()
except Exception:  # pragma: no cover - GPU may be unavailable
    pynvml = None  # type: ignore[assignment]

registry = DocumentRegistry()

_START_TIME = time.perf_counter()

if Gauge is not None and REGISTRY is not None:
    if "service_boot_duration_seconds" in REGISTRY._names_to_collectors:
        BOOT_DURATION_GAUGE = REGISTRY._names_to_collectors[
            "service_boot_duration_seconds"
        ]  # type: ignore[assignment]
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

if Gauge is not None and REGISTRY is not None:
    if "service_cpu_usage_percent" in REGISTRY._names_to_collectors:
        CPU_GAUGE = REGISTRY._names_to_collectors["service_cpu_usage_percent"]  # type: ignore[assignment]
    else:
        CPU_GAUGE = Gauge(
            "service_cpu_usage_percent",
            "CPU usage percentage",
            ["service"],
        )
    if "service_memory_usage_bytes" in REGISTRY._names_to_collectors:
        MEMORY_GAUGE = REGISTRY._names_to_collectors["service_memory_usage_bytes"]  # type: ignore[assignment]
    else:
        MEMORY_GAUGE = Gauge(
            "service_memory_usage_bytes",
            "Memory usage in bytes",
            ["service"],
        )
    if "service_gpu_memory_usage_bytes" in REGISTRY._names_to_collectors:
        GPU_GAUGE = REGISTRY._names_to_collectors["service_gpu_memory_usage_bytes"]  # type: ignore[assignment]
    else:
        GPU_GAUGE = Gauge(
            "service_gpu_memory_usage_bytes",
            "GPU memory usage in bytes",
            ["service"],
        )
else:
    CPU_GAUGE = MEMORY_GAUGE = GPU_GAUGE = None

if Histogram is not None and REGISTRY is not None:
    if "service_request_latency_seconds" in REGISTRY._names_to_collectors:
        LATENCY_HIST = REGISTRY._names_to_collectors["service_request_latency_seconds"]  # type: ignore[assignment]
    else:
        LATENCY_HIST = Histogram(
            "service_request_latency_seconds",
            "Request latency in seconds",
            ["service"],
        )
else:
    LATENCY_HIST = None

try:  # pragma: no cover - optional dependency
    from memory.chakra_registry import ChakraRegistry
except Exception:  # pragma: no cover - optional dependency
    ChakraRegistry = None  # type: ignore[assignment]
chakra_registry = ChakraRegistry() if ChakraRegistry is not None else None
"""Optional chakra registry; ``None`` if unavailable."""

if BOOT_DURATION_GAUGE is not None:
    BOOT_DURATION_GAUGE.labels("crown").set(time.perf_counter() - _START_TIME)


def route_decision(
    text: str,
    emotion_data: Dict[str, Any],
    orchestrator: MoGEOrchestrator | None = None,
    validator: EthicalValidator | None = None,
    *,
    documents: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """Return combined routing decision for ``text``.

    The function delegates model selection to :class:`MoGEOrchestrator` and
    chooses expression options based on both the current emotion and recent
    history.  Past ``expression_decision`` records are retrieved from the chakra
    registry and weighted higher when their stored ``soul_state``
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
    if heartbeat_monitor is not None:
        heartbeat_monitor.check_alerts()
        if heartbeat_monitor.sync_status() != "aligned":
            raise RuntimeError("chakras out of sync")
    if THROUGHPUT_COUNTER is not None:
        THROUGHPUT_COUNTER.labels("crown").inc()
    start = time.perf_counter()
    try:
        if validator is not None:
            validation = validator.validate_action("crown", text)
            if not validation.get("compliant", False):
                raise ValueError(
                    "ethical violation: "
                    + ", ".join(validation.get("violated_laws", []))
                )

        docs = documents or registry.get_corpus()

        protocol = os.getenv("INTERNAL_MODEL_PROTOCOL")
        if protocol == "mcp":
            try:
                from mcp.gateway import invoke_model as _mcp_invoke

                payload = json.dumps(
                    {
                        "text": text,
                        "emotion_data": emotion_data,
                        "documents": docs,
                    }
                )
                mcp_resp = asyncio.run(_mcp_invoke("orchestrator_route", payload))
                result = (
                    mcp_resp.get("result", {}) if isinstance(mcp_resp, dict) else {}
                )
            except Exception:
                orch = orchestrator or MoGEOrchestrator()
                result = orch.route(
                    text,
                    emotion_data,
                    text_modality=False,
                    voice_modality=False,
                    music_modality=False,
                    documents=docs,
                )
        else:
            orch = orchestrator or MoGEOrchestrator()
            result = orch.route(
                text,
                emotion_data,
                text_modality=False,
                voice_modality=False,
                music_modality=False,
                documents=docs,
            )

        emotion = emotion_data.get("emotion", "neutral")
        opts = decide_expression_options(emotion)

        soul = emotional_state.get_soul_state()
        if chakra_registry is not None:
            try:
                records = chakra_registry.search(
                    "crown",
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

    decision = {
        "model": result.get("model"),
        "tts_backend": tts_backend,
        "avatar_style": avatar_style,
        "aura": opts.get("aura"),
    }
    if chakra_registry is not None:
        try:  # pragma: no cover - best effort
            chakra_registry.record(
                "crown",
                text,
                "crown_router",
                type="expression_decision",
                emotion=emotion,
                tts_backend=tts_backend,
                avatar_style=avatar_style,
                soul_state=soul,
            )
        except Exception:
            pass
    duration = time.perf_counter() - start
    if LATENCY_HIST is not None:
        LATENCY_HIST.labels("crown").observe(duration)  # type: ignore[call-arg]
    if psutil is not None and CPU_GAUGE is not None and MEMORY_GAUGE is not None:
        CPU_GAUGE.labels("crown").set(psutil.cpu_percent())  # type: ignore[call-arg]
        MEMORY_GAUGE.labels("crown").set(psutil.virtual_memory().used)  # type: ignore[call-arg]
    if pynvml is not None and GPU_GAUGE is not None:
        try:  # pragma: no cover - GPU optional
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            GPU_GAUGE.labels("crown").set(mem_info.used)  # type: ignore[call-arg]
        except Exception:
            pass
    return decision


__all__ = ["route_decision"]
