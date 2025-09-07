from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Prepare stub modules before loading avatar_broadcast to avoid heavy imports
sys.modules.setdefault("video_stream", ModuleType("video_stream"))
sys.modules["video_stream"].session_manager = SimpleNamespace(
    get_tracks=lambda agent: (None, None)
)

spec = importlib.util.spec_from_file_location(
    "connectors.avatar_broadcast", ROOT / "connectors" / "avatar_broadcast.py"
)
avatar_broadcast = importlib.util.module_from_spec(spec)
sys.modules.setdefault("connectors", ModuleType("connectors"))
spec.loader.exec_module(avatar_broadcast)


class DummyTrack:
    async def recv(self) -> str:
        await asyncio.sleep(0)
        return "frame"


def test_broadcast_frame_and_heartbeat(monkeypatch) -> None:
    frames: list[tuple[str, str, dict | None]] = []
    beats: list[tuple[str, object, dict | None]] = []

    monkeypatch.setattr(
        avatar_broadcast.bot_discord,
        "send_frame",
        lambda frame, hb: frames.append(("discord", frame, hb)),
        raising=False,
    )
    monkeypatch.setattr(
        avatar_broadcast.bot_telegram,
        "send_frame",
        lambda chat, frame, hb: frames.append(("telegram", frame, hb)),
        raising=False,
    )
    monkeypatch.setattr(
        avatar_broadcast.bot_discord,
        "send_heartbeat",
        lambda agent, hb: beats.append(("discord", agent, hb)),
        raising=False,
    )
    monkeypatch.setattr(
        avatar_broadcast.bot_telegram,
        "send_heartbeat",
        lambda chat, hb: beats.append(("telegram", chat, hb)),
        raising=False,
    )

    monkeypatch.setattr(
        avatar_broadcast.session_manager,
        "get_tracks",
        lambda agent: (DummyTrack(), None),
    )

    async def fake_subscribe(handler, **kwargs):
        await handler(
            SimpleNamespace(
                agent_id="agent", event_type="heartbeat", payload={"chakra": "heart"}
            )
        )

    monkeypatch.setattr(avatar_broadcast, "subscribe", fake_subscribe)

    asyncio.run(
        avatar_broadcast.broadcast(
            "agent", discord_channel=1, telegram_chat=2, frame_limit=1
        )
    )

    assert frames == [
        ("discord", "frame", {"chakra": "heart"}),
        ("telegram", "frame", {"chakra": "heart"}),
    ]
    assert ("discord", "agent", {"chakra": "heart"}) in beats
    assert ("telegram", 2, {"chakra": "heart"}) in beats
