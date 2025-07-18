import asyncio
from pathlib import Path
import sys

import httpx
from fastapi.testclient import TestClient
from aiortc import RTCPeerConnection, RTCSessionDescription
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

import server


def test_webrtc_offer(monkeypatch):
    class DummyPC:
        def __init__(self) -> None:
            self.localDescription = RTCSessionDescription(sdp="x", type="answer")

        def addTransceiver(self, kind):
            pass

        def addTrack(self, track):
            pass

        async def setRemoteDescription(self, desc):
            pass

        async def createOffer(self):
            return RTCSessionDescription(sdp="o", type="offer")

        async def createAnswer(self):
            return self.localDescription

        async def setLocalDescription(self, desc):
            self.localDescription = desc

        async def close(self):
            pass

    monkeypatch.setattr(server.video_stream, "RTCPeerConnection", DummyPC)

    async def run() -> int:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                pc = RTCPeerConnection()
                pc.addTransceiver("video")
                pc.addTransceiver("audio")
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                resp = await client.post(
                    "/offer",
                    json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
                )
                await pc.close()
                return resp.status_code
    status = asyncio.run(run())
    assert status == 200
