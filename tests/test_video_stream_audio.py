import asyncio
from pathlib import Path
from types import ModuleType
import sys

import numpy as np
import httpx
from fastapi.testclient import TestClient
from aiortc import RTCSessionDescription
from aiortc.mediastreams import AUDIO_PTIME

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

import server
import video_stream


def test_avatar_audio_track(tmp_path):
    path = tmp_path / "t.wav"
    data = np.zeros(800, dtype=np.int16)
    import soundfile as sf
    sf.write(path, data, 8000)

    track = video_stream.AvatarAudioTrack(path)
    frame = asyncio.run(track.recv())
    assert frame.sample_rate == 8000
    arr = frame.to_ndarray()
    assert arr.shape[1] == int(8000 * AUDIO_PTIME)


def test_offer_adds_audio_track(monkeypatch):
    added = []

    class DummyPC:
        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="x", type="answer")

        def addTrack(self, track):
            added.append(type(track))

        async def setRemoteDescription(self, desc):
            pass

        async def createAnswer(self):
            return self.localDescription

        async def setLocalDescription(self, desc):
            self.localDescription = desc

        async def close(self):
            pass

    monkeypatch.setattr(video_stream, "RTCPeerConnection", DummyPC)

    async def run() -> int:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                resp = await client.post("/offer", json={"sdp": "x", "type": "offer"})
                return resp.status_code

    status = asyncio.run(run())
    assert status == 200
    assert video_stream.AvatarVideoTrack in added
    assert video_stream.AvatarAudioTrack in added


def test_server_shutdown_closes_peers(monkeypatch):
    events = []

    async def close_v():
        events.append("v")

    async def close_a():
        events.append("a")

    monkeypatch.setattr(server.video_stream, "close_peers", close_v)
    monkeypatch.setattr(server.webrtc_connector, "close_peers", close_a)

    with TestClient(server.app):
        pass

    assert "v" in events and "a" in events
