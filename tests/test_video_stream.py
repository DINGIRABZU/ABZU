"""Tests for the WebRTC video and audio streaming endpoints."""

from __future__ import annotations

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
_dummy_omegaconf = ModuleType("omegaconf")
_dummy_omegaconf.OmegaConf = object  # type: ignore[attr-defined]
_dummy_omegaconf.DictConfig = object  # type: ignore[attr-defined]
sys.modules.setdefault("omegaconf", _dummy_omegaconf)

import env_validation  # noqa: E402
import server  # noqa: E402
from crown_config import settings  # noqa: E402

settings.glm_command_token = "token"

pytestmark = pytest.mark.skipif(
    not env_validation.check_audio_binaries(require=False),
    reason="audio tools not installed",
)


def test_webrtc_offer(monkeypatch):
    class DummyPC:
        """Minimal RTCPeerConnection substitute tracking state."""

        instances = []

        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="x", type="answer")
            self.remoteDescription = None
            self.tracks: list[type] = []
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


def test_avatar_audio_track_default():
    """AvatarAudioTrack should generate silent audio by default."""

    track = server.video_stream.AvatarAudioTrack()
    frame = asyncio.run(track.recv())
    samples = int(server.video_stream.AUDIO_PTIME * 8000)
    assert frame.sample_rate == 8000
    assert frame.samples == samples
    assert not np.any(frame.to_ndarray())


def test_avatar_audio_requires_soundfile(monkeypatch, tmp_path):
    """Providing an audio path without soundfile installed raises an error."""

    monkeypatch.setattr(server.video_stream, "sf", None)
    with pytest.raises(RuntimeError, match="soundfile"):
        server.video_stream.AvatarAudioTrack(tmp_path / "x.wav")


def test_avatar_audio_endpoint_updates_track(monkeypatch, tmp_path):
    """The /avatar-audio endpoint should update the active track."""

    track = server.video_stream.AvatarVideoTrack()
    called: dict[str, Path] = {}

    def fake_update(path: Path) -> None:
        called["path"] = path

    monkeypatch.setattr(track, "update_audio", fake_update)
    server.video_stream._active_track = track

    audio = tmp_path / "clip.wav"
    audio.write_text("hi", encoding="utf-8")

    async def run() -> tuple[dict[str, str], int]:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                resp = await client.post("/avatar-audio", json={"path": str(audio)})
                return resp.json(), resp.status_code

    data, status = asyncio.run(run())
    server.video_stream._active_track = None

    assert status == 200
    assert data == {"status": "ok"}
    assert called["path"] == audio
