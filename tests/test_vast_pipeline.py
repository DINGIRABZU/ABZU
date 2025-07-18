from pathlib import Path
import asyncio
import sys
from types import ModuleType
import types

import numpy as np
import httpx
from fastapi.testclient import TestClient
from aiortc import RTCPeerConnection, RTCSessionDescription

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SPIRAL_OS"))
sf_mod = sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
setattr(sf_mod, "write", lambda *a, **k: None)
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)

import qnl_engine

sp_mod = sys.modules.setdefault("SPIRAL_OS", ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", qnl_engine)
sym_stub = ModuleType("symbolic_parser")
sym_stub.parse_intent = lambda d: []
sym_stub._gather_text = lambda d: d.get("text", "")
sym_stub._INTENTS = {}
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", sym_stub)
setattr(sp_mod, "qnl_engine", qnl_engine)
setattr(sp_mod, "symbolic_parser", sym_stub)

import server
import video_stream
from connectors import webrtc_connector
from orchestrator import MoGEOrchestrator
from core import language_engine, context_tracker


def test_hex_to_song_short_payload():
    phrases, wave = qnl_engine.hex_to_song("deadbeef", duration_per_byte=0.01, sample_rate=8000)
    assert phrases
    assert isinstance(wave, np.ndarray)
    assert wave.dtype == np.int16


def test_offer_returns_json_answer(monkeypatch):
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

    async def run() -> dict:
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
                return resp.json()

    data = asyncio.run(run())
    assert data["type"] == "answer"
    assert "sdp" in data


def test_start_call_triggered(monkeypatch):
    calls = []
    monkeypatch.setattr(webrtc_connector, "start_call", lambda p: calls.append(p))
    language_engine.register_connector(webrtc_connector)

    monkeypatch.setattr(language_engine.tts_coqui, "synthesize_speech", lambda t, e: f"/tmp/{e}.wav")
    monkeypatch.setattr("INANNA_AI.corpus_memory.search_corpus", lambda *a, **k: [("p", "s")])
    monkeypatch.setattr("orchestrator.vector_memory.add_vector", lambda *a, **k: None)
    monkeypatch.setattr("orchestrator.voice_aura.apply_voice_aura", lambda p, **k: p)
    monkeypatch.setattr("orchestrator.qnl_engine.hex_to_song", lambda *a, **k: ([], np.zeros(1, dtype=np.int16)))
    monkeypatch.setattr("orchestrator.qnl_engine.parse_input", lambda t: {"tone": "neutral"})
    monkeypatch.setattr("orchestrator.symbolic_parser.parse_intent", lambda d: [])
    monkeypatch.setattr("orchestrator.reflection_loop.run_reflection_loop", lambda *a, **k: None)
    monkeypatch.setattr("orchestrator.log_interaction", lambda *a, **k: None)
    monkeypatch.setattr("orchestrator.load_interactions", lambda: [])
    monkeypatch.setattr("orchestrator.update_insights", lambda logs: None)
    monkeypatch.setattr("orchestrator.load_insights", lambda: {})
    monkeypatch.setattr("orchestrator.learning_mutator.propose_mutations", lambda d: [])

    orch = MoGEOrchestrator()
    orch.handle_input("initiate sacred communion")
    assert context_tracker.state.in_call is True

    orch.route("hello", {"emotion": "joy"}, voice_modality=True)

    assert calls and calls[0] == "/tmp/joy.wav"
