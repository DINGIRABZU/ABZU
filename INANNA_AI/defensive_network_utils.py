"""Defensive network helpers for monitoring and secure POST requests."""
from __future__ import annotations

import logging
from pathlib import Path

from typing import Any

try:  # pragma: no cover - optional dependency
    from scapy.all import sniff, wrpcap  # type: ignore
except Exception:  # pragma: no cover - fallback when scapy missing
    sniff = None
    wrpcap = None

try:  # pragma: no cover - optional dependency
    import requests
except Exception:  # pragma: no cover - fallback when requests missing
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


def monitor_traffic(interface: str, packet_count: int = 5) -> None:
    """Capture packets from ``interface`` and store them in ``network_logs/defensive.pcap``."""
    if sniff is None or wrpcap is None:
        raise RuntimeError("scapy is required for packet capture")

    log_dir = Path("network_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    pcap_path = log_dir / "defensive.pcap"

    packets = sniff(iface=interface, count=packet_count)
    wrpcap(str(pcap_path), packets)
    logger.info("Captured %d packets to %s", len(packets), pcap_path)


def secure_communication(url: str, data: dict[str, Any]):
    """Send ``data`` via HTTPS POST to ``url`` with basic error handling.

    Returns the :class:`requests.Response` object on success.
    """
    if requests is None:
        raise RuntimeError("requests library is required for secure communication")

    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as exc:  # pragma: no cover - network errors
        logger.error("Failed to post to %s: %s", url, exc)
        raise
