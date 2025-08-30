#!/usr/bin/env python3
"""Audit key documents and log overdue reviews."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

__version__ = "0.1.0"

AUDIT_CADENCE_DAYS = {
    "Quarterly": 90,
    "Monthly": 30,
    "Annually": 365,
}


def parse_key_documents(key_doc_path: Path):
    """Return (name, path, cadence) tuples from KEY_DOCUMENTS.md."""
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)\s*\|\s*[^|]+\|\s*(\w+)")
    docs = []
    for line in key_doc_path.read_text().splitlines():
        match = pattern.search(line)
        if match:
            name, rel_path, cadence = match.groups()
            docs.append((name, rel_path.strip(), cadence))
    return docs


def main() -> None:
    """Log documents whose last modification exceeds their audit cadence."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    repo_root = Path(__file__).resolve().parent.parent
    key_docs_path = repo_root / "docs" / "KEY_DOCUMENTS.md"
    now = datetime.now()
    for name, rel_path, cadence in parse_key_documents(key_docs_path):
        cadence_days = AUDIT_CADENCE_DAYS.get(cadence)
        doc_path = (key_docs_path.parent / rel_path).resolve()
        if cadence_days is None or not doc_path.exists():
            logging.warning("Skipping %s (missing cadence or file)", name)
            continue
        mtime = datetime.fromtimestamp(doc_path.stat().st_mtime)
        if now - mtime > timedelta(days=cadence_days):
            logging.warning(
                "%s overdue for review (last updated %s)", name, mtime.date()
            )
        else:
            logging.info("%s reviewed on %s", name, mtime.date())


if __name__ == "__main__":
    main()
