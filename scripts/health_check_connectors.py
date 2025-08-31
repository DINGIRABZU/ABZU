"""Ping registered connectors and report readiness.

The script checks a predefined set of connector base URLs and queries their
``/health`` endpoints. A non-200 response or connection error marks a connector
as not ready. Results are printed as JSON and the process exits with status code
1 if any connector is unhealthy.
"""

from __future__ import annotations

__version__ = "0.1.0"

import json
import os
from typing import Dict

import requests


CONNECTORS: Dict[str, str] = {
    "operator_api": os.getenv("OPERATOR_API_URL", "http://localhost:8000"),
    "webrtc": os.getenv("WEBRTC_CONNECTOR_URL", "http://localhost:8000"),
    "primordials_api": os.getenv("PRIMORDIALS_API_URL", "http://localhost:8000"),
}


def _check(url: str) -> bool:
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def main() -> int:
    results = {name: _check(url) for name, url in CONNECTORS.items()}
    print(json.dumps(results))
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
