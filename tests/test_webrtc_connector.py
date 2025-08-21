import asyncio
import base64
from pathlib import Path
import sys
from types import ModuleType

import httpx
from fastapi.testclient import TestClient
from aiortc import RTCPeerConnection, RTCSessionDescription

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_utils", ModuleType("qnl_utils"))

import server
from connectors import webrtc_connector
from tests.data.short_wav_base64 import SHORT_WAV_BASE64
from crown_config import settings

settings.glm_command_token = "token"


def _write_audio(tmp_path: Path) -> Path:
    path = tmp_path / "short.wav"
    path.write_bytes(base64.b64decode(SHORT_WAV_BASE64))
    return path


def test_call_offer(monkeypatch):
    async def run() -> int:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                pc = RTCPeerConnection()
                pc.createDataChannel("audio")
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                resp = await client.post("/call", json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
                await pc.close()
                return resp.status_code
    status = asyncio.run(run())
    assert status == 200


def test_start_call_sends_audio(tmp_path):
    audio = _write_audio(tmp_path)
    messages = []

    async def run() -> None:
        with TestClient(server.app) as test_client:
            transport = httpx.ASGITransport(app=test_client.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                pc = RTCPeerConnection()
                channel = pc.createDataChannel("audio")

                @channel.on("message")
                def on_message(msg) -> None:
                    messages.append(msg)

                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                resp = await client.post("/call", json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type})
                answer = resp.json()
                await pc.setRemoteDescription(RTCSessionDescription(sdp=answer["sdp"], type=answer["type"]))
                await asyncio.sleep(0.1)
                webrtc_connector.start_call(str(audio))
                await asyncio.sleep(0.2)
                await webrtc_connector.close_peers()
                await pc.close()
    asyncio.run(run())
    assert messages and messages[0] == audio.read_bytes()


def test_close_peers_clears_state():
    class DummyPC:
        def __init__(self):
            self.closed = False

        async def close(self):
            self.closed = True

    class DummyChannel:
        def __init__(self):
            self.sent = []

        async def send(self, data):  # pragma: no cover - not used
            self.sent.append(data)

    pc = DummyPC()
    ch = DummyChannel()
    webrtc_connector._pcs = {pc}
    webrtc_connector._channels = {ch}
    asyncio.run(webrtc_connector.close_peers())

    assert pc.closed
    assert not webrtc_connector._pcs and not webrtc_connector._channels
