"""Tests for simultaneous avatar sessions and heartbeat emission."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import ModuleType
import sys

from citadel.event_producer import Event, EventProducer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
_dummy_omegaconf = ModuleType("omegaconf")
_dummy_omegaconf.OmegaConf = object  # type: ignore[attr-defined]
_dummy_omegaconf.DictConfig = object  # type: ignore[attr-defined]
sys.modules.setdefault("omegaconf", _dummy_omegaconf)

import video_stream  # noqa: E402  # isort:skip
from agents.event_bus import set_event_producer  # noqa: E402  # isort:skip


class DummyProducer(EventProducer):
    def __init__(self) -> None:  # pragma: no cover - simple container
        self.events: list[Event] = []

    async def emit(self, event: Event) -> None:  # pragma: no cover - simple
        self.events.append(event)


def test_multi_session_heartbeat(monkeypatch) -> None:
    """Multiple sessions should emit heartbeat events for their agents."""

    producer = DummyProducer()
    set_event_producer(producer)

    manager = video_stream.AvatarSessionManager(interval=0.01)
    video_stream.session_manager = manager
    video_stream.processor.session_manager = manager

    # Avoid heavy track dependencies
    monkeypatch.setattr(video_stream, "enable_audio_track", False, raising=False)
    monkeypatch.setattr(video_stream, "enable_video_track", False, raising=False)

    async def run() -> None:
        manager.get_tracks("memory_scribe")
        manager.get_tracks("prompt_orchestrator")
        await asyncio.sleep(0.05)
        manager.remove("memory_scribe")
        manager.remove("prompt_orchestrator")
        await asyncio.sleep(0)

    asyncio.run(run())

    agents = {e.agent_id for e in producer.events if e.event_type == "heartbeat"}
    assert {"memory_scribe", "prompt_orchestrator"} <= agents
    chakras = {
        e.payload.get("chakra") for e in producer.events if e.event_type == "heartbeat"
    }
    assert "heart" in chakras and "throat" in chakras

    set_event_producer(None)
