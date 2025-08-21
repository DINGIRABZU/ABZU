import asyncio
import sys
from pathlib import Path
from types import ModuleType

import httpx
import numpy as np
import pytest
from aiortc import RTCPeerConnection, RTCSessionDescription
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

from crown_config import settings

settings.glm_command_token = "token"

import env_validation

pytestmark = pytest.mark.skipif(
    not env_validation.check_audio_binaries(require=False),
    reason="audio tools not installed",
)

import server


def test_webrtc_offer(monkeypatch):
    class DummyPC:
        """Minimal RTCPeerConnection substitute tracking state."""

        instances = []

        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="x", type="answer")
            self.remoteDescription = None
            self.tracks = []
            self.closed = False
            DummyPC.instances.append(self)

        def addTrack(self, track):
            self.tracks.append(type(track))

        async def setRemoteDescription(self, desc):
            self.remoteDescription = desc

        async def createOffer(self):
            return RTCSessionDescription(sdp="o", type="offer")

        async def createAnswer(self):
            return self.localDescription

        async def setLocalDescription(self, desc):
            self.localDescription = desc

        async def close(self):
            self.closed = True

    monkeypatch.setattr(server.video_stream, "RTCPeerConnection", DummyPC)

    async def run() -> int:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                pc = RTCPeerConnection()
                pc.addTransceiver("video")
                pc.addTransceiver("audio")
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                resp = await client.post(
                    "/offer",
                    json={
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type,
                    },
                )
                await pc.close()
                return resp.status_code

    status = asyncio.run(run())
    # Close server-side peer to test cleanup side effects
    asyncio.run(server.video_stream.close_peers())

    assert status == 200
    assert len(DummyPC.instances) == 1
    pc_state = DummyPC.instances[0]
    # Remote description from the offer should be recorded
    assert pc_state.remoteDescription and pc_state.remoteDescription.type == "offer"
    # Server should attach both video and audio tracks
    assert server.video_stream.AvatarVideoTrack in pc_state.tracks
    assert server.video_stream.AvatarAudioTrack in pc_state.tracks
    # Peer connection should be closed after calling close_peers
    assert pc_state.closed
    # All peer connections should be cleared from the registry
    assert not server.video_stream._pcs


def test_avatar_video_track_frames(monkeypatch):
    """AvatarVideoTrack should yield frames from the video engine."""

    frames = [
        np.zeros((1, 1, 3), dtype=np.uint8),
        np.ones((1, 1, 3), dtype=np.uint8),
    ]
    calls = {"n": 0}

    def fake_stream():
        calls["n"] += 1
        for f in frames:
            yield f

    monkeypatch.setattr(
        server.video_stream.video_engine, "generate_avatar_stream", fake_stream
    )

    track = server.video_stream.AvatarVideoTrack()
    frame1 = asyncio.run(track.recv()).to_ndarray()
    frame2 = asyncio.run(track.recv()).to_ndarray()

    assert calls["n"] == 1  # stream created once
    assert np.array_equal(frame1, frames[0])
    assert np.array_equal(frame2, frames[1])
    # No more frames should remain in the stream
    with pytest.raises(RuntimeError):
        asyncio.run(track.recv())
