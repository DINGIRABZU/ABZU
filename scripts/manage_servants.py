from __future__ import annotations

"""Utility to download, start, health-check, and stop servant models."""

__version__ = "0.1.0"

import argparse
import json
import os
import signal
import subprocess
from pathlib import Path
from typing import Dict, List

import requests  # type: ignore[import-untyped]

STATE_FILE = Path("data/servant_state.json")

_STATE: Dict[str, Dict[str, int | bool]] = {"pids": {}, "health": {}}


def _load_state() -> None:
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            _STATE["pids"].update({k: int(v) for k, v in data.get("pids", {}).items()})
            _STATE["health"].update(
                {k: bool(v) for k, v in data.get("health", {}).items()}
            )
        except (OSError, json.JSONDecodeError):
            pass


def _save_state() -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with STATE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(_STATE, fh)


def download_servant(name: str, url: str, dest: Path) -> None:
    """Download servant model weights to *dest*."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)


def start_servant(name: str, command: List[str]) -> None:
    """Start servant subprocess given by *command* and record its PID."""
    proc = subprocess.Popen(command)
    _STATE["pids"][name] = proc.pid
    _save_state()


def health_check_servant(name: str, url: str) -> bool:
    """Update and return health status for *name* by hitting *url*."""
    try:
        resp = requests.get(url, timeout=5)
        healthy = resp.status_code == 200
    except requests.RequestException:
        healthy = False
    _STATE["health"][name] = healthy
    _save_state()
    return healthy


def stop_servant(name: str) -> None:
    """Stop servant process for *name* if running."""
    pid = _STATE["pids"].get(name)
    if pid:
        try:
            os.kill(int(pid), signal.SIGTERM)
        except OSError:
            pass
        _STATE["pids"].pop(name, None)
        _save_state()


def is_servant_healthy(name: str) -> bool:
    """Return last recorded health status for *name*."""
    return bool(_STATE["health"].get(name, False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage servant models")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_dl = sub.add_parser("download", help="Download servant model")
    p_dl.add_argument("name")
    p_dl.add_argument("url")
    p_dl.add_argument("path")

    p_start = sub.add_parser("start", help="Start servant process")
    p_start.add_argument("name")
    p_start.add_argument("command", nargs=argparse.REMAINDER)

    p_health = sub.add_parser("health", help="Health check servant")
    p_health.add_argument("name")
    p_health.add_argument("url")

    p_stop = sub.add_parser("stop", help="Stop servant process")
    p_stop.add_argument("name")

    args = parser.parse_args()
    _load_state()

    if args.cmd == "download":
        download_servant(args.name, args.url, Path(args.path))
    elif args.cmd == "start":
        start_servant(args.name, args.command)
    elif args.cmd == "health":
        healthy = health_check_servant(args.name, args.url)
        print("healthy" if healthy else "unhealthy")
    elif args.cmd == "stop":
        stop_servant(args.name)


if __name__ == "__main__":  # pragma: no cover
    main()
