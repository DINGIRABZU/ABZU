"""Tests for razar health checks."""

from unittest import mock


from razar import health_checks as hc


def _fake_ready_response(status="ready"):
    class FakeResp:
        def __init__(self, status_code=200, payload=None):
            self.status = status_code
            self._payload = payload or {"status": status}

        def read(self):
            import json

            return json.dumps(self._payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    return FakeResp()


def test_ready_signal_parses_status(monkeypatch):
    def fake_urlopen(url, timeout=5):
        assert url.endswith("/ready")
        return _fake_ready_response("ready")

    monkeypatch.setattr(hc.urllib.request, "urlopen", fake_urlopen)
    assert hc.check_inanna_ready()
    assert hc.check_crown_ready()

    def fake_urlopen_bad(url, timeout=5):
        return _fake_ready_response("waiting")

    monkeypatch.setattr(hc.urllib.request, "urlopen", fake_urlopen_bad)
    assert not hc.check_inanna_ready()


def test_run_attempts_restart(monkeypatch):
    calls = {"count": 0}

    def check():
        calls["count"] += 1
        return calls["count"] > 1

    monkeypatch.setitem(hc.CHECKS, "demo", check)
    monkeypatch.setitem(hc.RESTART_COMMANDS, "demo", ["bash", "-c", "true"])

    run_mock = mock.Mock()
    monkeypatch.setattr(hc.subprocess, "run", run_mock)

    assert hc.run("demo") is True
    run_mock.assert_called_once()
