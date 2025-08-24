"""Configuration helpers for network utilities."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

CONFIG_FILE = (
    Path(__file__).resolve().parents[2]
    / "INANNA_AI_AGENT"
    / "network_utils_config.json"
)

_DEFAULT_CONFIG = {
    "log_dir": "network_logs",
    "capture_file": "network_logs/capture.pcap",
}


def load_config() -> dict:
    """Return configuration for network utilities."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())

    try:
        resource_path = resources.files("INANNA_AI") / "network_utils_config.json"
        if resource_path.is_file():
            return json.loads(resource_path.read_text())
    except Exception:
        pass

    return _DEFAULT_CONFIG.copy()


__all__ = ["CONFIG_FILE", "load_config"]
