import sys
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import system_monitor


def test_collect_stats(monkeypatch):
    class Mem:
        percent = 50.0

    class Net:
        bytes_sent = 100
        bytes_recv = 200

    monkeypatch.setattr(system_monitor.psutil, "cpu_percent", lambda interval=None: 25.0)
    monkeypatch.setattr(system_monitor.psutil, "virtual_memory", lambda: Mem)
    monkeypatch.setattr(system_monitor.psutil, "net_io_counters", lambda: Net)

    stats = system_monitor.collect_stats()
    assert stats == {
        "cpu_percent": 25.0,
        "memory_percent": 50.0,
        "bytes_sent": 100,
        "bytes_recv": 200,
    }


def test_watch_loop(monkeypatch, capsys):
    calls = []

    def fake_collect():
        calls.append(True)
        if len(calls) > 1:
            raise KeyboardInterrupt()
        return {"cpu_percent": 1}

    monkeypatch.setattr(system_monitor, "collect_stats", fake_collect)
    monkeypatch.setattr(system_monitor.time, "sleep", lambda t: None)

    system_monitor._print_stats_loop(0)
    out = capsys.readouterr().out.strip()
    assert out == json.dumps({"cpu_percent": 1})
