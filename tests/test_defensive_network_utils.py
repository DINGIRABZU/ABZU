import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import defensive_network_utils as dnu
from INANNA_AI.defensive_network_utils import monitor_traffic, secure_communication


def test_monitor_traffic(tmp_path, monkeypatch):
    calls = {}

    def sniff(iface=None, count=0):
        calls['iface'] = iface
        calls['count'] = count
        return ['pkt'] * count

    def wrpcap(path, packets):
        calls['path'] = path
        calls['packets'] = packets
        Path(path).write_text('data')

    monkeypatch.setattr('INANNA_AI.defensive_network_utils.sniff', sniff)
    monkeypatch.setattr('INANNA_AI.defensive_network_utils.wrpcap', wrpcap)
    monkeypatch.chdir(tmp_path)

    monitor_traffic('eth0', packet_count=3)

    pcap = tmp_path / 'network_logs' / 'defensive.pcap'
    assert pcap.exists()
    assert calls == {
        'iface': 'eth0',
        'count': 3,
        'path': 'network_logs/defensive.pcap',
        'packets': ['pkt', 'pkt', 'pkt'],
    }


def test_secure_communication(monkeypatch):
    resp = SimpleNamespace(status_code=200, text='ok')
    resp.raise_for_status = lambda: None
    calls = {}

    dummy = ModuleType('requests')
    dummy.RequestException = Exception

    def post(url, json=None, timeout=None):
        calls['url'] = url
        calls['json'] = json
        calls['timeout'] = timeout
        return resp

    dummy.post = post
    monkeypatch.setitem(sys.modules, 'requests', dummy)
    monkeypatch.setattr(dnu, 'requests', dummy)

    out = secure_communication('https://example.com', {'a': 1})
    assert out is resp
    assert calls == {
        'url': 'https://example.com',
        'json': {'a': 1},
        'timeout': 10,
    }


def test_secure_communication_error(monkeypatch):
    class DummyExc(Exception):
        pass

    dummy = ModuleType('requests')
    dummy.RequestException = DummyExc

    def post(url, json=None, timeout=None):
        raise DummyExc('fail')

    dummy.post = post
    monkeypatch.setitem(sys.modules, 'requests', dummy)
    monkeypatch.setattr(dnu, 'requests', dummy)

    with pytest.raises(DummyExc):
        secure_communication('https://bad.com', {'x': 1})

