"""Bio-adaptive narrator using biosignal streams to craft stories.

This module ingests biosignals via :mod:`biosppy` and uses a
:mod:`transformers` text generation pipeline to narrate the subject's
state. The main entry point is :func:`generate_story`.
"""

from __future__ import annotations

import threading
import time
from typing import Iterable

import numpy as np
import requests

try:  # pragma: no cover - optional dependency
    from biosppy.signals import ecg
except Exception:  # pragma: no cover - dependency may be missing
    ecg = None  # type: ignore

from ..event_bus import emit_event
from memory import narrative_engine
from spiral_memory import DEFAULT_MEMORY
from connectors.primordials_api import send_metrics

try:  # pragma: no cover - optional dependency
    from prometheus_client import Gauge, Histogram, REGISTRY
except Exception:  # pragma: no cover - optional dependency
    Gauge = Histogram = REGISTRY = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import pynvml

    pynvml.nvmlInit()
except Exception:  # pragma: no cover - GPU may be unavailable
    pynvml = None  # type: ignore[assignment]

__version__ = "0.0.2"

CHAKRA = "third_eye"
CHAKRACON_URL = "http://localhost:8080"
THRESHOLD_HEART_RATE = 120.0

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


def fetch_metrics() -> dict:
    resp = requests.get(f"{CHAKRACON_URL}/metrics/{CHAKRA}", timeout=5)
    resp.raise_for_status()
    return resp.json()


def monitor_metrics(poll_interval: float = 5.0) -> None:
    while True:
        data = fetch_metrics()
        value = data.get("heart_rate", 0.0)
        if value > THRESHOLD_HEART_RATE:
            emit_event("bana", "heart_rate_high", {"value": value})
        time.sleep(poll_interval)


def start_monitoring(poll_interval: float = 5.0) -> threading.Thread:
    thread = threading.Thread(
        target=monitor_metrics, args=(poll_interval,), daemon=True
    )
    thread.start()
    return thread


try:  # pragma: no cover - optional dependency
    from transformers import pipeline  # type: ignore
except Exception:  # pragma: no cover - dependency may be missing

    def pipeline(*args, **kwargs):  # type: ignore
        raise ImportError("transformers pipeline unavailable") from None


def generate_story(bio_stream: Iterable[float], sampling_rate: float = 1000.0) -> str:
    """Generate a short story from a biosignal stream.

    Parameters
    ----------
    bio_stream:
        Sequence of raw biosignal samples such as ECG.

    Returns
    -------
    str
        Narrative text describing the subject.
    """
    start = time.perf_counter()
    samples = np.asarray(list(bio_stream), dtype=float)
    if samples.size == 0:
        raise ValueError("bio_stream must contain at least one sample")
    if sampling_rate <= 0:
        raise ValueError("sampling_rate must be positive")
    if samples.size < int(sampling_rate):
        raise ValueError("bio_stream length must be >= sampling_rate")

    if ecg is None:
        raise ImportError("biosppy is required for ECG processing")

    # Extract heart rate using biosppy. The function returns a namedtuple or
    # dict; both provide a ``heart_rate`` entry.
    result = ecg.ecg(signal=samples, sampling_rate=sampling_rate, show=False)
    heart_rate = (
        result.get("heart_rate")
        if isinstance(result, dict)
        else getattr(result, "heart_rate", [])
    )
    avg_rate = float(np.mean(heart_rate)) if np.size(heart_rate) else 60.0

    prompt = (
        f"The subject's heart beats at {avg_rate:.1f} BPM. "
        "Compose a reflective tale about their journey."
    )

    try:
        generator = pipeline("text-generation", model="distilgpt2")
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("transformers pipeline unavailable") from exc

    text = generator(prompt, max_new_tokens=30, num_return_sequences=1)[0][
        "generated_text"
    ]
    narrative_engine.log_story(text)
    DEFAULT_MEMORY.register_event(text, layers={"quality": [float(len(text))]})
    send_metrics({"story_length": len(text)})
    duration = time.perf_counter() - start
    if LATENCY_HIST is not None:
        LATENCY_HIST.labels("bana").observe(duration)  # type: ignore[call-arg]
    if psutil is not None and CPU_GAUGE is not None and MEMORY_GAUGE is not None:
        CPU_GAUGE.labels("bana").set(psutil.cpu_percent())  # type: ignore[call-arg]
        MEMORY_GAUGE.labels("bana").set(psutil.virtual_memory().used)  # type: ignore[call-arg]
    if pynvml is not None and GPU_GAUGE is not None:
        try:  # pragma: no cover - GPU optional
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            GPU_GAUGE.labels("bana").set(mem_info.used)  # type: ignore[call-arg]
        except Exception:
            pass
    return text


__all__ = ["generate_story", "start_monitoring", "__version__"]
