"""Ping registered connectors and optional remote agents.

The script checks a predefined set of connector base URLs and queries their
``/health`` endpoints. A non-200 response or connection error marks a connector
as not ready. When ``--include-remote`` is supplied the script also performs a
lightweight POST against the Kimi K2, AirStar, and rStar endpoints using sample
payloads derived from the public repositories. Results are printed as JSON and
the process exits with status code 1 if any connector is unhealthy.

When invoked from automation (for example, ``scripts/rehearsal_scheduler.py``)
the module emits a richer report that includes HTTP status codes, probe latency,
and timestamps for downstream dashboards and alerting rules.
"""

from __future__ import annotations

__version__ = "0.4.0"

import argparse
import json
import logging
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping

import requests

LOGGER_NAME = "monitoring.alerts.razar_failover"
logger = logging.getLogger(LOGGER_NAME)

ALERTS_PATH = (
    Path(__file__).resolve().parents[1] / "monitoring" / "alerts" / "razar_failover.yml"
)

CONNECTORS: Dict[str, str] = {
    "operator_api": os.getenv("OPERATOR_API_URL", "http://localhost:8000"),
    "webrtc": os.getenv("WEBRTC_CONNECTOR_URL", "http://localhost:8000"),
    "primordials_api": os.getenv("PRIMORDIALS_API_URL", "http://localhost:8000"),
}

REMOTE_AGENT_ENV: Dict[str, tuple[str, str]] = {
    "kimi2": ("KIMI2_ENDPOINT", "KIMI2_API_KEY"),
    "airstar": ("AIRSTAR_ENDPOINT", "AIRSTAR_API_KEY"),
    "rstar": ("RSTAR_ENDPOINT", "RSTAR_API_KEY"),
}

_WEATHER_PROMPT = (
    "What's the weather like in Beijing today? Let's check using the tool."
)
_WEATHER_DESCRIPTION = (
    "Retrieve current weather information. Call this when the user asks about the"
    " weather."
)

REMOTE_AGENT_PAYLOADS: Mapping[str, Dict[str, Any]] = {
    "kimi2": {
        "model": "moonshotai/Kimi-K2-Instruct",
        "messages": [
            {
                "role": "user",
                "content": _WEATHER_PROMPT,
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": _WEATHER_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "required": ["city"],
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City to query",
                            }
                        },
                    },
                },
            }
        ],
        "temperature": 0.6,
        "max_tokens": 512,
    },
    "airstar": {
        "model": "moonshotai/Kimi-K2-Instruct",
        "messages": [
            {
                "role": "user",
                "content": _WEATHER_PROMPT,
            }
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": _WEATHER_DESCRIPTION,
                    "parameters": {
                        "type": "object",
                        "required": ["city"],
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City to query",
                            }
                        },
                    },
                },
            }
        ],
        "temperature": 0.6,
        "max_tokens": 512,
        "context": {
            "component": "crown_router",
            "error": "Health check failed",
            "attempt": 1,
        },
    },
    "rstar": {
        "model": "rstar/qwen3-14b",
        "prompt": [940, 1265, 8123, 102],
        "temperature": 1.0,
        "max_tokens": 8192,
        "skip_special_tokens": False,
        "include_stop_str_in_output": True,
    },
}


def _iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def _probe_connector(name: str, url: str) -> Dict[str, Any]:
    start = time.perf_counter()
    response: requests.Response | None = None
    error: str | None = None
    status_code: int | None = None

    try:
        response = requests.get(f"{url.rstrip('/')}/health", timeout=5)
        status_code = getattr(response, "status_code", None)
        ok = status_code == 200
    except Exception as exc:  # pragma: no cover - network failures => unhealthy
        error = str(exc)
        ok = False
    else:
        if status_code != 200:
            logger.warning("Connector probe returned %s for %s", status_code, url)
        ok = status_code == 200

    elapsed = time.perf_counter() - start

    if error:
        logger.warning("Connector probe failed for %s: %s", url, error)

    return {
        "name": name,
        "ok": ok,
        "status_code": status_code,
        "latency_seconds": elapsed,
        "url": url,
        "error": error,
        "checked_at": _iso_now(),
        "probe": "GET /health",
        "kind": "connector",
    }


def _remote_payload(name: str) -> Dict[str, Any]:
    return deepcopy(REMOTE_AGENT_PAYLOADS[name])


def _probe_remote_agent(name: str, endpoint: str, token: str | None) -> Dict[str, Any]:
    payload = _remote_payload(name)
    headers: Dict[str, str] = {}

    if token:
        payload["auth_token"] = token
        headers["Authorization"] = f"Bearer {token}"
        headers["X-API-Key"] = token

    start = time.perf_counter()
    response: requests.Response | None = None
    error: str | None = None
    status_code: int | None = None

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers or None,
            timeout=10,
        )
        status_code = getattr(response, "status_code", None)
        response.raise_for_status()
        ok = True
    except Exception as exc:  # pragma: no cover - network failures
        error = str(exc)
        ok = False
        status_code = getattr(
            getattr(exc, "response", None), "status_code", status_code
        )
        logger.warning(
            "Remote agent %s probe failed: %s (see %s)",
            name,
            exc,
            ALERTS_PATH,
        )
    else:
        logger.info(
            "Remote agent %s responded with %s (see %s)",
            name,
            status_code,
            ALERTS_PATH,
        )

    elapsed = time.perf_counter() - start

    return {
        "name": name,
        "ok": ok,
        "status_code": status_code,
        "latency_seconds": elapsed,
        "endpoint": endpoint,
        "error": error,
        "checked_at": _iso_now(),
        "probe": "POST",
        "kind": "remote",
        "token_present": bool(token),
    }


def _check_remote_agents() -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for name, (endpoint_env, token_env) in REMOTE_AGENT_ENV.items():
        endpoint = os.getenv(endpoint_env)
        if not endpoint:
            logger.debug("Skipping %s probe; %s is unset", name, endpoint_env)
            continue
        token = os.getenv(token_env) or None
        results[name] = _probe_remote_agent(name, endpoint, token)
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Connector health probes")
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help=(
            "Include MoonshotAI Kimi K2 / AirStar and Microsoft rStar probes "
            "when endpoints are configured."
        ),
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Print the full health report (status codes, latency, timestamps).",
    )
    return parser.parse_args(argv)


def collect_health_reports(
    *, include_remote: bool = False
) -> Dict[str, Dict[str, Any]]:
    """Return detailed connector and optional remote agent probe results."""

    _configure_logging()

    results = {name: _probe_connector(name, url) for name, url in CONNECTORS.items()}
    if include_remote:
        results.update(_check_remote_agents())

    return results


def run_health_checks(*, include_remote: bool = False) -> Dict[str, bool]:
    """Return connector and optional remote agent health probe results."""

    reports = collect_health_reports(include_remote=include_remote)
    return {name: bool(report.get("ok")) for name, report in reports.items()}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.detailed:
        results: Mapping[str, Any] = collect_health_reports(
            include_remote=args.include_remote
        )
    else:
        results = run_health_checks(include_remote=args.include_remote)

    print(json.dumps(results, sort_keys=True))

    if not results:
        return 1

    if args.detailed:
        return 0 if all(bool(item.get("ok")) for item in results.values()) else 1

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
