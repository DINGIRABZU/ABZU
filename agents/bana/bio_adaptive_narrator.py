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

__version__ = "0.0.2"

CHAKRA = "third_eye"
CHAKRACON_URL = "http://localhost:8080"
THRESHOLD_HEART_RATE = 120.0


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
    return text


__all__ = ["generate_story", "start_monitoring", "__version__"]
