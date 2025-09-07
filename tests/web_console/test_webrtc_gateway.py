"""Integration tests for the unified WebRTC gateway."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import ModuleType
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))
_dummy_omegaconf = ModuleType("omegaconf")
_dummy_omegaconf.OmegaConf = object  # type: ignore[attr-defined]
_dummy_omegaconf.DictConfig = object  # type: ignore[attr-defined]
sys.modules.setdefault("omegaconf", _dummy_omegaconf)

from aiortc import RTCSessionDescription
from fastapi import FastAPI
from fastapi.testclient import TestClient

from communication import webrtc_gateway


def test_offer_and_avatar_audio(monkeypatch, tmp_path):
    class DummyPC:
        """Minimal RTCPeerConnection substitute tracking added tracks."""

        instances: list["DummyPC"] = []

        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="x", type="answer")
            self.remoteDescription = None
            self.tracks: list[type] = []
            DummyPC.instances.append(self)

        def addTrack(self, track):  # noqa: N802 - mimic aiortc API
            self.tracks.append(type(track))

        async def setRemoteDescription(self, desc):  # noqa: N802
            self.remoteDescription = desc

        async def createAnswer(self):  # noqa: N802
            return self.localDescription

        async def setLocalDescription(self, desc):  # noqa: N802
            self.localDescription = desc

        async def close(self):  # pragma: no cover - dummy close
            pass

    monkeypatch.setattr(webrtc_gateway, "RTCPeerConnection", DummyPC)

    app = FastAPI()
    app.include_router(webrtc_gateway.router)

    with TestClient(app) as client:
        resp = client.post("/offer", json={"sdp": "v=0", "type": "offer"})
        assert resp.status_code == 200
        pc = DummyPC.instances[0]
        assert webrtc_gateway.AvatarVideoTrack in pc.tracks
        assert webrtc_gateway.AvatarAudioTrack in pc.tracks

        active = webrtc_gateway._active_track  # type: ignore[attr-defined]
        assert active is not None
        called: dict[str, Path] = {}

        def fake_update(path: Path) -> None:
            called["path"] = path

        active.update_audio = fake_update  # type: ignore[assignment]
        audio_path = tmp_path / "test.wav"
        resp = client.post("/avatar-audio", json={"path": str(audio_path)})
        assert resp.status_code == 200
        assert called["path"] == audio_path

    asyncio.run(webrtc_gateway.close_peers())
