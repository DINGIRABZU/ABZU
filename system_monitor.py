#!/usr/bin/env python3
"""System resource monitoring utilities."""
from __future__ import annotations

import argparse
import json
import time
from typing import Any, Dict

import psutil


def collect_stats() -> Dict[str, Any]:
    """Gather basic CPU, memory and network usage statistics."""
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    net = psutil.net_io_counters()
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": mem.percent,
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
    }


def _print_stats_loop(interval: float) -> None:
    """Continuously print system stats until interrupted."""
    try:
        while True:
            print(json.dumps(collect_stats()))
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="System monitor")
    parser.add_argument("--watch", action="store_true", help="continuously display stats")
    parser.add_argument(
        "--interval", type=float, default=1.0, help="refresh interval when watching"
    )
    args = parser.parse_args(argv)

    if args.watch:
        _print_stats_loop(args.interval)
    else:
        print(json.dumps(collect_stats()))


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
