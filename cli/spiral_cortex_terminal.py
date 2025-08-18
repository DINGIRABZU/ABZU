from __future__ import annotations

"""Command line tool for exploring ``cortex_memory_spiral.jsonl``."""

from collections import Counter
import argparse
import time
from typing import Dict, Iterable

import cortex_memory
from archetype_feedback_loop import evaluate_archetype


def _parse_filters(pairs: Iterable[str]) -> Dict[str, str]:
    filters: Dict[str, str] = {}
    for pair in pairs:
        if "=" in pair:
            key, val = pair.split("=", 1)
            filters[key] = val
    return filters


def _load_entries(filters: Dict[str, str], limit: int) -> list[dict]:
    entries = cortex_memory.query_spirals(filters)
    if limit:
        entries = entries[-limit:]
    return entries


def _print_entries(entries: Iterable[dict]) -> None:
    for e in entries:
        ts = e.get("timestamp", "")
        decision = e.get("decision", {})
        emotion = decision.get("emotion", "")
        event = decision.get("event", "")
        print(f"{ts} | emotion={emotion} | event={event}")


def run_query(filters: Dict[str, str], limit: int) -> None:
    """Print entries matching ``filters``."""
    entries = _load_entries(filters, limit)
    _print_entries(entries)


def run_dreamwalk(filters: Dict[str, str], limit: int) -> None:
    """Display entries one by one with short delays."""
    entries = _load_entries(filters, limit)
    for e in entries:
        _print_entries([e])
        time.sleep(1)


def run_stats(filters: Dict[str, str], limit: int) -> None:
    """Show emotion and event statistics and archetype suggestion."""
    entries = _load_entries(filters, limit)
    emotions: list[str] = []
    events: list[str] = []
    for e in entries:
        dec = e.get("decision", {})
        emotions.append(dec.get("emotion", ""))
        events.append(dec.get("event", ""))

    emot_counts = Counter([e for e in emotions if e])
    event_counts = Counter([e for e in events if e])

    if emot_counts:
        print("Emotion counts:")
        for emo, count in emot_counts.most_common():
            print(f" - {emo}: {count}")
    if event_counts:
        print("Event counts:")
        for ev, count in event_counts.most_common():
            print(f" - {ev}: {count}")

    recommendation = evaluate_archetype(limit=limit or 10)
    if recommendation:
        print(f"Suggested archetype shift: {recommendation}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Explore spiral cortex memory")
    parser.add_argument(
        "--query",
        nargs="*",
        metavar="KEY=VAL",
        help="Filter decision fields (e.g. emotion=joy)",
    )
    parser.add_argument(
        "--dreamwalk",
        action="store_true",
        help="Print entries sequentially with delays",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Display emotion trends and archetype suggestion",
    )
    parser.add_argument("--limit", type=int, default=0, help="Number of entries")
    args = parser.parse_args(argv)

    filters = _parse_filters(args.query or [])
    if args.dreamwalk:
        run_dreamwalk(filters, args.limit)
    elif args.stats:
        run_stats(filters, args.limit)
    else:
        run_query(filters, args.limit)


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
