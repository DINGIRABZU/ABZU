from pathlib import Path
import sys
import types
import importlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_voice_cli_invokes_engines(tmp_path, monkeypatch):
    audio = tmp_path / "voice.wav"
    audio.write_text("x", encoding="utf-8")
    events = {}

    class DummySpeaker:
        def synthesize(self, text: str, emotion: str, history=None, timbre="neutral"):
            events["synth"] = (text, emotion)
            return str(audio)

    monkeypatch.setitem(
        sys.modules,
        "INANNA_AI.speaking_engine",
        types.SimpleNamespace(SpeakingEngine=lambda: DummySpeaker()),
    )

    def fake_stream(path: Path):
        events["stream"] = path
        yield b"f"

    monkeypatch.setitem(
        sys.modules,
        "core.avatar_expression_engine",
        types.SimpleNamespace(stream_avatar_audio=fake_stream),
    )

    webrtc_stub = types.ModuleType("connectors.webrtc_connector")
    webrtc_stub.start_call = lambda p: events.setdefault("call", p)
    webrtc_stub.router = None
    webrtc_stub.close_peers = None
    connectors_pkg = types.ModuleType("connectors")
    connectors_pkg.webrtc_connector = webrtc_stub
    connectors_pkg.webrtc_start_call = webrtc_stub.start_call
    connectors_pkg.webrtc_router = None
    connectors_pkg.webrtc_close_peers = None
    monkeypatch.setitem(sys.modules, "connectors.webrtc_connector", webrtc_stub)
    monkeypatch.setitem(sys.modules, "connectors", connectors_pkg)

    mod = importlib.import_module("inanna_voice")
    argv_backup = sys.argv.copy()
    sys.argv = [
        "inanna_voice.py",
        "hello",
        "--emotion",
        "joy",
        "--play",
        "--call",
    ]
    try:
        mod.main()
    finally:
        sys.argv = argv_backup

    assert events["synth"] == ("hello", "joy")
    assert events["call"] == str(audio)
    assert events["stream"] == audio
