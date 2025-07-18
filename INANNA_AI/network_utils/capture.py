"""Packet capture helpers using scapy or pyshark."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from . import load_config

try:  # pragma: no cover - optional dependency
    from scapy.all import sniff, wrpcap  # type: ignore
except Exception:  # pragma: no cover - fallback
    sniff = None
    wrpcap = None


logger = logging.getLogger(__name__)


def capture_packets(interface: str, *, count: int = 20, output: Optional[str] = None) -> None:
    """Capture ``count`` packets from ``interface`` and write them to ``output``."""
    cfg = load_config()
    out_path = Path(output or cfg.get("capture_file", "capture.pcap"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if sniff is None or wrpcap is None:
        raise RuntimeError("scapy is required for packet capture")

    packets = sniff(iface=interface, count=count)
    wrpcap(str(out_path), packets)
    logger.info("Captured %d packets to %s", len(packets), out_path)
