# pydocstyle: skip-file
"""Command line utilities for managing spiral memory."""

from __future__ import annotations

__version__ = "0.1.1"

import argparse
from pathlib import Path

from . import cortex


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_prune = sub.add_parser("prune", help="Prune memory to keep N latest entries")
    p_prune.add_argument("keep", type=int, help="Number of latest entries to keep")

    p_export = sub.add_parser("export", help="Export entries to a JSON file")
    p_export.add_argument("path", help="Output file path")
    p_export.add_argument("--tags", nargs="*", help="Semantic tags to filter")

    p_query = sub.add_parser("query", help="Query entries and print as JSON")
    p_query.add_argument("--tags", nargs="*", help="Semantic tags to filter")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cmd == "prune":
        cortex.prune_spirals(args.keep)
    elif args.cmd == "export":
        cortex.export_spirals(Path(args.path), tags=args.tags)
    elif args.cmd == "query":
        res = cortex.query_spirals(tags=args.tags)
        import json

        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
