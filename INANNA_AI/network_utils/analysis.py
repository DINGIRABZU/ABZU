"""Basic traffic analysis for PCAP files."""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

from . import load_config

try:  # pragma: no cover - optional dependency
    from scapy.all import rdpcap  # type: ignore
except Exception:  # pragma: no cover - fallback
    rdpcap = None


logger = logging.getLogger(__name__)


def analyze_capture(pcap_path: str, *, log_dir: Optional[str] = None) -> dict:
    """Return a simple summary of the packets in ``pcap_path`` and save a log."""
    if rdpcap is None:
        raise RuntimeError("scapy is required for analysis")

    packets = rdpcap(pcap_path)
    proto_counts: Counter[str] = Counter()
    talkers: Counter[str] = Counter()
    for pkt in packets:
        proto_counts[pkt.__class__.__name__] += 1
        src = getattr(pkt, "src", None)
        if src:
            talkers[src] += 1

    top_talkers = [[addr, count] for addr, count in talkers.most_common(5)]
    summary = {
        "total_packets": len(packets),
        "protocols": dict(proto_counts),
        "top_talkers": top_talkers,
    }

    cfg = load_config()
    log_directory = Path(log_dir or cfg.get("log_dir", "network_logs"))
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "summary.log"
    log_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Saved summary to %s", log_file)
    return summary
