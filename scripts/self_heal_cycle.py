from __future__ import annotations

"""Simple self-healing cycle for quarantined components.

This script scans ``logs/razar_state.json`` for component failures, delegates
recovery to :func:`razar.ai_invoker.handover`, validates the resulting patch in a
throwaway Docker container, and records the outcome.
"""

from datetime import datetime
import json
import subprocess
import uuid
from pathlib import Path
from typing import Iterable, Tuple

from razar import ai_invoker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = PROJECT_ROOT / "logs" / "razar_state.json"
SELF_HEAL_LOG = PROJECT_ROOT / "logs" / "self_heal.jsonl"
QUARANTINE_LOG = PROJECT_ROOT / "docs" / "quarantine_log.md"


def _load_failures(path: Path = STATE_FILE) -> Iterable[Tuple[str, str]]:
    """Yield ``(component, error)`` pairs for failed components."""
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    events = data.get("events", [])
    failures: list[Tuple[str, str]] = []
    for event in events:
        if event.get("status") == "fail" and event.get("component"):
            failures.append((event["component"], event.get("error", "")))
    return failures


def _append_logs(component: str, success: bool, details: str) -> None:
    """Append outcome to JSON log and quarantine markdown."""
    timestamp = datetime.utcnow().isoformat()
    SELF_HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": timestamp,
        "component": component,
        "success": success,
        "details": details,
    }
    with SELF_HEAL_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

    action = "patched" if success else "patch_failed"
    QUARANTINE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with QUARANTINE_LOG.open("a", encoding="utf-8") as md:
        md.write(f"| {timestamp} | {component} | {action} | {details} |\n")


def _build_and_test() -> Tuple[bool, str]:
    """Build a temporary Docker image and run tests."""
    tag = f"self-heal-{uuid.uuid4().hex[:8]}"
    try:
        build = subprocess.run(
            ["docker", "build", "-t", tag, str(PROJECT_ROOT)],
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            return False, f"docker build failed: {build.stderr.strip()}"
        run = subprocess.run(
            ["docker", "run", "--rm", tag, "pytest"],
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            return False, f"tests failed: {run.stderr.strip()}"
        return True, run.stdout.strip()
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, text=True)


def main() -> int:
    failures = list(_load_failures())
    if not failures:
        print("No failures detected")
        return 0
    for component, error in failures:
        patched = ai_invoker.handover(component, error)
        success = False
        details = ""
        if patched:
            success, details = _build_and_test()
        _append_logs(component, success and patched, details or "no patch applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
