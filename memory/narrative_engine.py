# pydocstyle: skip-file
"""Persistent narrative memory engine.

Provides interfaces for recording story events composed of an actor,
action and symbolism.

Stories and structured events are stored in a SQLite database with optional
Chroma vector persistence so narratives survive process restarts and
support semantic search.
"""

from __future__ import annotations

__version__ = "0.4.0"

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import json
import uuid
import time
from typing import Iterable, Iterator, Optional, Dict, Any, Callable

try:  # pragma: no cover - optional dependency
    import chromadb
    from chromadb.api import Collection
except Exception:  # pragma: no cover - optional dependency
    chromadb = None  # type: ignore

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

if BOOT_DURATION_GAUGE is not None:
    BOOT_DURATION_GAUGE.labels("memory").set(time.perf_counter() - _START_TIME)

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "narrative_engine.db"
CHROMA_DIR = Path(__file__).resolve().parents[1] / "data" / "narrative_events.chroma"


@dataclass
class StoryEvent:
    """A story beat linking an actor, an action and optional symbolism."""

    actor: str
    action: str
    symbolism: str | None = None


def compose_multitrack_story(
    events: Iterable[StoryEvent],
    *,
    stream: bool = False,
    emotion: str = "neutral",
    frame_callback: Callable[[Any], None] | None = None,
) -> Dict[str, Any]:
    """Compose cinematic, audio, visual and USD tracks from ``events``.

    Parameters
    ----------
    events:
        Sequence of :class:`StoryEvent` objects forming the narrative.
    stream:
        If ``True`` the prose is spoken via :mod:`core.expressive_output` and
        avatar frames are streamed to ``frame_callback``.
    emotion:
        Vocal style passed to the speech synthesizer when ``stream`` is
        enabled.
    frame_callback:
        Optional callback receiving avatar frames. Ignored if ``stream`` is
        ``False``.

    Returns
    -------
    dict
        Dictionary with ``prose``, ``audio``, ``visual`` and ``usd`` tracks.
    """

    prose = [f"{e.actor} {e.action}." for e in events]
    audio = [{"cue": f"{e.actor}_{e.action}".replace(" ", "_")} for e in events]
    visual = [{"directive": f"frame {e.actor} {e.action}"} for e in events]
    usd = [{"op": "AddPrim", "path": f"/{e.actor}", "action": e.action} for e in events]
    tracks = {
        "prose": " ".join(prose),
        "audio": audio,
        "visual": visual,
        "usd": usd,
    }
    if stream:
        from core import expressive_output

        if frame_callback is not None:
            expressive_output.set_frame_callback(frame_callback)
        expressive_output.speak(tracks["prose"], emotion)
    return tracks


class NarrativeEngine:
    """Interface for working with narrative story events."""

    def record(self, event: StoryEvent) -> None:  # pragma: no cover - interface stub
        """Record a story event in the narrative store."""
        raise NotImplementedError

    def stream(self) -> Iterable[StoryEvent]:  # pragma: no cover - interface stub
        """Iterate over stored story events."""
        raise NotImplementedError


def _get_conn() -> sqlite3.Connection:
    """Return connection to the story database, creating schema if needed."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS stories ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "text TEXT NOT NULL"
        ")"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events ("
        "id TEXT PRIMARY KEY, "
        "time TEXT NOT NULL, "
        "agent_id TEXT NOT NULL, "
        "event_type TEXT NOT NULL, "
        "payload TEXT NOT NULL"
        ")"
    )
    return conn


def _get_collection() -> Collection:
    """Return ChromaDB collection for events."""

    if chromadb is None:  # pragma: no cover - optional dependency
        raise RuntimeError("chromadb library not installed")
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection("events")


def log_story(text: str) -> None:
    """Persist ``text`` to the story log."""
    if THROUGHPUT_COUNTER is not None:
        THROUGHPUT_COUNTER.labels("memory").inc()
    try:
        with _get_conn() as conn:
            conn.execute("INSERT INTO stories (text) VALUES (?)", (text,))
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("memory").inc()
        raise


def stream_stories() -> Iterable[str]:
    """Yield recorded stories in insertion order."""

    with _get_conn() as conn:
        for (text,) in conn.execute("SELECT text FROM stories ORDER BY id"):
            yield text


def log_event(event: Dict[str, Any]) -> None:
    """Persist a structured ``event`` to SQLite and ChromaDB."""
    start = time.perf_counter()
    if THROUGHPUT_COUNTER is not None:
        THROUGHPUT_COUNTER.labels("memory").inc()
    try:
        event_id = uuid.uuid4().hex
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO events (id, time, agent_id, event_type, payload) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    event_id,
                    event["time"],
                    event["agent_id"],
                    event["event_type"],
                    json.dumps(event["payload"]),
                ),
            )
        if chromadb is not None:  # pragma: no cover - optional dependency
            collection = _get_collection()
            collection.add(
                ids=[event_id],
                documents=[
                    json.dumps({"event_type": event["event_type"], **event["payload"]})
                ],
            )
    except Exception:
        if ERROR_COUNTER is not None:
            ERROR_COUNTER.labels("memory").inc()
        raise
    finally:
        duration = time.perf_counter() - start
        if LATENCY_HIST is not None:
            LATENCY_HIST.labels("memory").observe(duration)  # type: ignore[call-arg]
        if psutil is not None and CPU_GAUGE is not None and MEMORY_GAUGE is not None:
            CPU_GAUGE.labels("memory").set(psutil.cpu_percent())  # type: ignore[call-arg]
            MEMORY_GAUGE.labels("memory").set(psutil.virtual_memory().used)  # type: ignore[call-arg]
        if pynvml is not None and GPU_GAUGE is not None:
            try:  # pragma: no cover - GPU optional
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                GPU_GAUGE.labels("memory").set(mem_info.used)  # type: ignore[call-arg]
            except Exception:
                pass


def query_events(
    *, agent_id: Optional[str] = None, event_type: Optional[str] = None
) -> Iterator[Dict[str, Any]]:
    """Yield events filtered by ``agent_id`` and/or ``event_type``."""

    sql = "SELECT id, time, agent_id, event_type, payload FROM events"
    clauses: list[str] = []
    params: list[Any] = []
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY time"
    with _get_conn() as conn:
        for _id, time, ag, et, payload in conn.execute(sql, params):
            yield {
                "id": _id,
                "time": time,
                "agent_id": ag,
                "event_type": et,
                "payload": json.loads(payload),
            }


def search_events(query_text: str, n_results: int = 5) -> Iterator[Dict[str, Any]]:
    """Vector search ``query_text`` against stored events using ChromaDB."""

    if chromadb is None:  # pragma: no cover - optional dependency
        raise RuntimeError("chromadb library not installed")
    collection = _get_collection()
    results = collection.query(query_texts=[query_text], n_results=n_results)
    ids = results.get("ids", [[]])[0]
    with _get_conn() as conn:
        for event_id in ids:
            row = conn.execute(
                "SELECT id, time, agent_id, event_type, payload FROM events "
                "WHERE id = ?",
                (event_id,),
            ).fetchone()
            if row:
                _id, time, ag, et, payload = row
                yield {
                    "id": _id,
                    "time": time,
                    "agent_id": ag,
                    "event_type": et,
                    "payload": json.loads(payload),
                }


__all__ = [
    "StoryEvent",
    "NarrativeEngine",
    "log_story",
    "stream_stories",
    "log_event",
    "compose_multitrack_story",
    "query_events",
    "search_events",
    "DB_PATH",
    "CHROMA_DIR",
]
