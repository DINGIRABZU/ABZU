"""Command line entry for network utilities."""
from __future__ import annotations

import argparse
import logging
import time

from .capture import capture_packets
from .analysis import analyze_capture
from . import schedule_capture


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Network monitoring tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    cap = sub.add_parser("capture", help="Capture packets from an interface")
    cap.add_argument("interface")
    cap.add_argument("--count", type=int, default=20)
    cap.add_argument("--output")

    ana = sub.add_parser("analyze", help="Summarize a pcap file")
    ana.add_argument("pcap")
    ana.add_argument("--log-dir")

    sched = sub.add_parser("schedule", help="Capture packets periodically")
    sched.add_argument("interface")
    sched.add_argument("--period", type=float, default=60.0)

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if args.cmd == "capture":
        capture_packets(args.interface, count=args.count, output=args.output)
    elif args.cmd == "analyze":
        analyze_capture(args.pcap, log_dir=args.log_dir)
    elif args.cmd == "schedule":
        schedule_capture(args.interface, args.period)
        print(
            f"Scheduled capture on {args.interface} every {args.period} seconds."
        )
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
