#!/usr/bin/env python3
"""Log user feedback to the local database."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from INANNA_AI import db_storage


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Record feedback metrics")
    parser.add_argument("emotion", help="Detected emotion")
    parser.add_argument("satisfaction", type=float, help="Satisfaction score")
    parser.add_argument("alignment", type=float, help="Ethical alignment score")
    parser.add_argument("clarity", type=float, help="Existential clarity score")
    parser.add_argument(
        "--db", default=str(db_storage.DB_PATH), help="Database path"
    )
    args = parser.parse_args(argv)

    db_storage.log_feedback(
        args.emotion,
        args.satisfaction,
        args.alignment,
        args.clarity,
        db_path=Path(args.db),
    )
    print("Feedback recorded.")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    main()
