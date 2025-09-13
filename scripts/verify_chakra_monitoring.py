"""Verify chakra monitoring setup and metric emission."""

from __future__ import annotations

import os
import socket
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # pragma: no cover - fallback for standalone execution
    from agents.razar import health_checks
except ModuleNotFoundError:  # pragma: no cover - agents package optional
    health_checks = None  # type: ignore[assignment]

__version__ = "0.1.0"
DEFAULT_EXPORTERS = [
    "http://localhost:9101/metrics",  # node exporter
    "http://localhost:8080/metrics",  # cadvisor
    "http://localhost:9400/metrics",  # gpu exporter
]


def _fetch(url: str, timeout: float = 2.0) -> bool:
    """Return ``True`` if ``url`` returns any content."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # nosec B310
            if resp.status >= 400:
                return False
            body = resp.read()
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"failed to query {url}: {exc}", file=sys.stderr)
        return False
    return bool(body.strip())


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("localhost", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _check_agent_metrics() -> bool:
    """Run a doc sync check and confirm metrics are exposed."""
    if health_checks is None:
        return True
    port = _find_free_port()
    health_checks.init_metrics(port)
    # run a cheap check that should succeed
    health_checks.run("razar_doc_sync_agent")
    # wait briefly for server thread
    for _ in range(5):
        try:
            with urllib.request.urlopen(
                f"http://localhost:{port}"
            ) as resp:  # nosec B310
                text = resp.read().decode()
            return "service_health_status" in text
        except Exception:  # pragma: no cover - network dependent
            time.sleep(0.1)
    return False


def _check_docs() -> list[str]:
    docs = ROOT / "docs"
    errors: list[str] = []
    if not (docs / "chakra_metrics.md").exists():
        errors.append("missing docs/chakra_metrics.md")
    if not (docs / "The_Absolute_Protocol.md").exists():
        errors.append("missing docs/The_Absolute_Protocol.md")
    return errors


def verify_chakra_monitoring() -> int:
    """Exit non-zero when monitoring invariants are violated."""
    urls_env = os.getenv("CHAKRA_EXPORTERS")
    exporters = (
        [u.strip() for u in urls_env.split(",")] if urls_env else DEFAULT_EXPORTERS
    )
    missing = [url for url in exporters if not _fetch(url)]
    if missing:
        for url in missing:
            print(f"missing metrics from exporter {url}", file=sys.stderr)
    if health_checks is None:
        print(
            "agents package not available; skipping agent metrics check",
            file=sys.stderr,
        )
    elif not _check_agent_metrics():
        print("agent metrics not emitted", file=sys.stderr)
        missing.append("agent metrics")
    doc_errors = _check_docs()
    if doc_errors:
        for err in doc_errors:
            print(err, file=sys.stderr)
    if missing or doc_errors:
        return 1
    print("verify_chakra_monitoring: all checks passed")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(verify_chakra_monitoring())
