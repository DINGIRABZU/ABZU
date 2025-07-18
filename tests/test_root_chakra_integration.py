import sys
import json
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy dependencies similar to other integration tests
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
sys.modules["numpy"].int16 = "int16"
sys.modules["numpy"].float32 = float
sys.modules["numpy"].ndarray = object
scipy_mod = types.ModuleType("scipy")
scipy_io = types.ModuleType("scipy.io")
wavfile_mod = types.ModuleType("scipy.io.wavfile")
wavfile_mod.write = lambda *a, **k: None
scipy_io.wavfile = wavfile_mod
scipy_mod.io = scipy_io
signal_mod = types.ModuleType("scipy.signal")
signal_mod.butter = lambda *a, **k: (None, None)
signal_mod.lfilter = lambda *a, **k: []
scipy_mod.signal = signal_mod
sys.modules.setdefault("scipy.signal", signal_mod)
mod_sf = types.ModuleType("soundfile")
mod_sf.write = lambda *a, **k: None
sys.modules.setdefault("scipy", scipy_mod)
sys.modules.setdefault("scipy.io", scipy_io)
sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
sys.modules.setdefault("soundfile", mod_sf)
stable_mod = types.ModuleType("stable_baselines3")
stable_mod.PPO = lambda *a, **k: object()
gym_mod = types.ModuleType("gymnasium")
gym_mod.Env = object
gym_mod.spaces = types.SimpleNamespace(Box=lambda **k: None)
sys.modules.setdefault("stable_baselines3", stable_mod)
sys.modules.setdefault("gymnasium", gym_mod)

from INANNA_AI_AGENT import INANNA_AI
import system_monitor
from INANNA_AI import network_utils


def test_root_chakra_flow(tmp_path, monkeypatch):
    # --- invoke inanna_ai CLI to generate QNL song ---
    wav = tmp_path / "song.wav"
    js = tmp_path / "song.json"
    argv_backup = sys.argv.copy()
    sys.argv = [
        "INANNA_AI.py",
        "--hex",
        "01ff",
        "--wav",
        str(wav),
        "--json",
        str(js),
    ]
    monkeypatch.setattr(
        inanna_ai,
        "run_qnl",
        lambda *a, **k: (wav.write_text(""), js.write_text("{}")),
    )
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup
    assert wav.exists()
    assert js.exists()

    # --- collect system stats and write log ---
    class Mem:
        percent = 42.0

    class Net:
        bytes_sent = 1
        bytes_recv = 2

    monkeypatch.setattr(system_monitor.psutil, "cpu_percent", lambda interval=None: 99.9)
    monkeypatch.setattr(system_monitor.psutil, "virtual_memory", lambda: Mem)
    monkeypatch.setattr(system_monitor.psutil, "net_io_counters", lambda: Net)

    stats = system_monitor.collect_stats()
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    log_file = log_dir / "system_status.json"
    log_file.write_text(json.dumps(stats))
    assert log_file.exists()
    assert json.loads(log_file.read_text()) == stats

    # --- schedule network capture and ensure triggered ---
    calls = []
    timers = []

    def fake_capture(interface, count=20, output=None):
        calls.append(interface)

    class DummyTimer:
        def __init__(self, delay, func):
            self.delay = delay
            self.func = func
            timers.append(self)

        def start(self):
            pass

        def cancel(self):
            pass

    monkeypatch.setattr(network_utils, "capture_packets", fake_capture)
    monkeypatch.setattr(network_utils, "threading", types.SimpleNamespace(Timer=DummyTimer))

    timer = network_utils.schedule_capture("eth0", 2)
    assert isinstance(timer, DummyTimer)
    timer.func()

    assert calls == ["eth0"]
    assert len(timers) == 2
