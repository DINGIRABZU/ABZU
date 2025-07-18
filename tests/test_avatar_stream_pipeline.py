import sys
from pathlib import Path
import types
import numpy as np
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Patch heavy optional dependencies before importing modules
aiortc_stub = types.ModuleType("aiortc")
class DummyDesc:
    def __init__(self, sdp: str, type: str) -> None:
        self.sdp = sdp
        self.type = type
class DummyPC:
    def __init__(self) -> None:
        self.localDescription = DummyDesc("ans", "answer")
    def addTransceiver(self, kind: str) -> None:
        pass
    def addTrack(self, track: object) -> None:
        pass
    async def setRemoteDescription(self, desc: DummyDesc) -> None:
        pass
    async def createOffer(self) -> DummyDesc:
        return DummyDesc("off", "offer")
    async def createAnswer(self) -> DummyDesc:
        return self.localDescription
    async def setLocalDescription(self, desc: DummyDesc) -> None:
        self.localDescription = desc
    async def close(self) -> None:
        pass
class VideoStreamTrack:
    kind = "video"
    async def recv(self):
        pass
class AudioStreamTrack:
    kind = "audio"
    async def recv(self):
        pass
AUDIO_PTIME = 0.02
aiortc_stub.RTCPeerConnection = DummyPC
aiortc_stub.RTCSessionDescription = DummyDesc
aiortc_stub.VideoStreamTrack = VideoStreamTrack
aiortc_stub.AudioStreamTrack = AudioStreamTrack
mediastreams_mod = types.ModuleType("aiortc.mediastreams")
mediastreams_mod.AUDIO_PTIME = AUDIO_PTIME
mediastreams_mod.AudioStreamTrack = AudioStreamTrack
mediastreams_mod.MediaStreamError = Exception
sys.modules.setdefault("aiortc", aiortc_stub)
sys.modules.setdefault("aiortc.mediastreams", mediastreams_mod)

librosa_stub = types.ModuleType("librosa")
librosa_stub.load = lambda *a, **k: (np.zeros(10, dtype=np.float32), 8000)
sys.modules.setdefault("librosa", librosa_stub)

sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sent_mod = types.ModuleType("sentence_transformers")
sent_mod.SentenceTransformer = lambda *a, **k: None
sys.modules.setdefault("sentence_transformers", sent_mod)
scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
scipy_mod.io = scipy_io
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.signal", signal_mod)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
yaml_mod = types.ModuleType("yaml")
yaml_mod.safe_load = lambda *a, **k: {}
sys.modules.setdefault("yaml", yaml_mod)
sp_mod = sys.modules.setdefault("SPIRAL_OS", types.ModuleType("SPIRAL_OS"))
sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))
sys.modules.setdefault("SPIRAL_OS.symbolic_parser", types.ModuleType("symbolic_parser"))
stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: object()
gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
gym_mod.spaces = types.SimpleNamespace(Box=lambda **k: None)
sys.modules.setdefault("stable_baselines3", stable_mod)
sys.modules.setdefault("gymnasium", gym_mod)

tts_mod = types.ModuleType("TTS")
api_mod = types.ModuleType("api")
class DummyTTS:
    def __init__(self, *a, **k) -> None:
        pass
    def tts_to_file(self, text: str, file_path: str, speaker: str = "random", speed: float = 1.0) -> None:
        Path(file_path).write_bytes(b"dummy")
api_mod.TTS = DummyTTS
tts_mod.api = api_mod
sys.modules.setdefault("TTS", tts_mod)

sf_stub = types.ModuleType("soundfile")
sf_stub.read = lambda *a, **k: (np.zeros(1, dtype=np.int16), 8000)
sf_stub.write = lambda *a, **k: None
sys.modules.setdefault("soundfile", sf_stub)

from orchestrator import MoGEOrchestrator
import orchestrator
from INANNA_AI import tts_xtts, tts_coqui
from core import avatar_expression_engine, video_engine
import audio_engine
import server
import vector_memory
import crown_decider
import voice_aura


def test_avatar_stream_pipeline(tmp_path, monkeypatch):
    wav = tmp_path / "speech.wav"

    # Stub synthesis to produce a short wav
    def fake_synth(text: str, emotion: str) -> str:
        wav.write_bytes(b"RIFF00")
        return str(wav)
    monkeypatch.setattr(tts_xtts, "synthesize", fake_synth)
    monkeypatch.setattr(tts_coqui, "synthesize_speech", fake_synth)

    # Stub other components
    monkeypatch.setattr(audio_engine, "play_sound", lambda p, loop=False: None)
    monkeypatch.setattr(video_engine, "start_stream", lambda lip_sync_audio=None: iter([np.zeros((1, 1, 3), dtype=np.uint8)]))
    monkeypatch.setattr(avatar_expression_engine.emotional_state, "get_last_emotion", lambda: "joy")
    monkeypatch.setattr(voice_aura, "apply_voice_aura", lambda p, **k: p)
    monkeypatch.setattr(crown_decider, "decide_expression_options", lambda e: {"tts_backend": "xtts", "avatar_style": "A", "aura_amount": 0.1, "soul_state": "awakened"})

    logs = []
    monkeypatch.setattr(vector_memory, "add_vector", lambda text, meta: logs.append(meta))
    monkeypatch.setattr(vector_memory, "query_vectors", lambda *a, **k: [])

    orch = MoGEOrchestrator()
    result = orch.route("hello", {"emotion": "joy"}, text_modality=False, voice_modality=True)

    voice_path = Path(result["voice_path"])
    assert voice_path.exists()

    stream = avatar_expression_engine.stream_avatar_audio(voice_path, fps=1)
    frame = next(stream)
    assert frame.size > 0
    for _ in stream:
        pass

    assert any(m.get("type") == "expression_decision" for m in logs)

    monkeypatch.setattr(server.video_stream, "RTCPeerConnection", DummyPC)
    with TestClient(server.app) as client:
        resp = client.post("/offer", json={"sdp": "x", "type": "offer"})
        assert resp.status_code == 200
