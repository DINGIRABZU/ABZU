import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.network_utils import capture_packets
from INANNA_AI.network_utils import analyze_capture, load_config


def _dummy_packet(proto: str, src: str | None = None):
    cls = type(proto, (), {})
    pkt = cls()
    if src:
        setattr(pkt, "src", src)
    return pkt


def test_capture_packets(tmp_path, monkeypatch):
    calls = {}

    def sniff(iface=None, count=0):
        calls["iface"] = iface
        calls["count"] = count
        return ["pkt"] * count

    def wrpcap(path, packets):
        calls["path"] = path
        calls["packets"] = packets
        Path(path).write_text("data")

    monkeypatch.setattr("INANNA_AI.network_utils.capture.sniff", sniff)
    monkeypatch.setattr("INANNA_AI.network_utils.capture.wrpcap", wrpcap)

    out = tmp_path / "cap.pcap"
    capture_packets("eth0", count=3, output=str(out))

    assert out.exists()
    assert calls == {
        "iface": "eth0",
        "count": 3,
        "path": str(out),
        "packets": ["pkt", "pkt", "pkt"],
    }


def test_analyze_capture(tmp_path, monkeypatch):
    packets = [
        _dummy_packet("TCP", "1.1.1.1"),
        _dummy_packet("UDP", "2.2.2.2"),
        _dummy_packet("TCP", "1.1.1.1"),
    ]

    def rdpcap(path):
        assert path == "dummy.pcap"
        return packets

    log_dir = tmp_path / "logs"
    monkeypatch.setattr("INANNA_AI.network_utils.analysis.rdpcap", rdpcap)
    monkeypatch.setattr(
        "INANNA_AI.network_utils.analysis.load_config", lambda: {"log_dir": str(log_dir)}
    )

    summary = analyze_capture("dummy.pcap")
    assert summary["total_packets"] == 3
    assert summary["protocols"] == {"TCP": 2, "UDP": 1}
    assert summary["top_talkers"][0][0] == "1.1.1.1"

    log_file = log_dir / "summary.log"
    assert log_file.exists()
    assert json.loads(log_file.read_text()) == summary


def test_load_config_from_resource(tmp_path, monkeypatch):
    cfg = tmp_path / "network_utils_config.json"
    cfg.write_text(json.dumps({"log_dir": "x", "capture_file": "y"}))
    import INANNA_AI.network_utils as nu
    monkeypatch.setattr(nu.resources, "files", lambda pkg: tmp_path)
    monkeypatch.setattr(nu, "CONFIG_FILE", tmp_path / "missing.json")
    assert load_config() == {"log_dir": "x", "capture_file": "y"}


def test_load_config_missing(monkeypatch):
    import INANNA_AI.network_utils as nu
    monkeypatch.setattr(nu.resources, "files", lambda pkg: Path('missing'))
    monkeypatch.setattr(nu, "CONFIG_FILE", Path('missing'))
    assert load_config() == {"log_dir": "network_logs", "capture_file": "network_logs/capture.pcap"}
