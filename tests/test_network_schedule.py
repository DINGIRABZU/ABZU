import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.network_utils import schedule_capture


def test_schedule_capture(monkeypatch):
    calls = []

    def capture(interface, count=20, output=None):
        calls.append(interface)

    timers = []

    class DummyTimer:
        def __init__(self, delay, func):
            self.delay = delay
            self.func = func
            timers.append(self)
        def start(self):
            # do nothing
            pass
        def cancel(self):
            pass

    monkeypatch.setattr('INANNA_AI.network_utils.threading.Timer', DummyTimer)
    monkeypatch.setattr('INANNA_AI.network_utils.capture_packets', capture)

    timer = schedule_capture('eth0', 2)
    assert isinstance(timer, DummyTimer)
    assert timer.delay == 2
    # manually invoke to simulate timer firing
    timer.func()

    assert calls == ['eth0']
    # second timer scheduled
    assert len(timers) == 2
    assert timers[1].delay == 2

