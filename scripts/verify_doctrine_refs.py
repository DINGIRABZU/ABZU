from __future__ import annotations

"""Ensure doctrine documents are referenced in ``docs/INDEX.md``.

The script checks that ``docs/INDEX.md`` links to the following
key documents:

* ``The_Absolute_Protocol.md``
* ``blueprint_spine.md``
* ``docs/error_registry.md``
* ``docs/testing/failure_inventory.md``

It exits with a non-zero status when any reference is missing,
printing the missing paths. Intended for use as a pre-commit hook.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "The_Absolute_Protocol.md",
    "blueprint_spine.md",
    "error_registry.md",
    "testing/failure_inventory.md",
]


def verify_doctrine_refs(root: Path | None = None) -> None:
    """Validate that all required docs appear in ``docs/INDEX.md``."""
    base = Path(root) if root else ROOT
    index_path = base / "docs" / "INDEX.md"
    if not index_path.exists():
        print("missing docs/INDEX.md", file=sys.stderr)
        raise SystemExit(1)

    index_text = index_path.read_text(encoding="utf-8")
    missing = [name for name in REQUIRED if name not in index_text]
    if missing:
        for name in missing:
            print(f"{name} not listed in docs/INDEX.md", file=sys.stderr)
        raise SystemExit(1)
    print("verify_doctrine_refs: all checks passed")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    verify_doctrine_refs()
