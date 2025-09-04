from __future__ import annotations

"""Audit core documentation doctrine.

This script enforces several documentation invariants:

* ``docs/The_Absolute_Protocol.md`` mentions the rule to read
  ``blueprint_spine.md`` three times.
* ``docs/INDEX.md`` lists ``The_Absolute_Protocol.md``, ``blueprint_spine.md``,
  ``error_registry.md`` and ``testing/failure_inventory.md``.
* ``docs/error_registry.md`` and ``docs/testing/failure_inventory.md`` exist
  and are non-empty.

The script exits with a non-zero status and prints failing checks when any
invariant is violated. Intended for use as a pre-commit hook.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

BLUEPRINT_RULE = "read [blueprint_spine.md](blueprint_spine.md) three times"


def audit_doctrine(root: Path | None = None) -> None:
    """Validate documentation doctrine under *root* (defaults to repo root)."""
    base = Path(root) if root else ROOT
    docs = base / "docs"
    errors: list[str] = []

    protocol_path = docs / "The_Absolute_Protocol.md"
    if not protocol_path.exists():
        errors.append(f"missing {protocol_path}")
    else:
        text = protocol_path.read_text(encoding="utf-8").lower()
        if BLUEPRINT_RULE.lower() not in text:
            errors.append(
                "The_Absolute_Protocol.md missing 'read blueprint_spine.md three times' rule"
            )

    index_path = docs / "INDEX.md"
    if not index_path.exists():
        errors.append("missing docs/INDEX.md")
    else:
        index_text = index_path.read_text(encoding="utf-8")
        for name in (
            "The_Absolute_Protocol.md",
            "blueprint_spine.md",
            "error_registry.md",
            "testing/failure_inventory.md",
        ):
            if name not in index_text:
                errors.append(f"{name} not listed in INDEX.md")

    for rel in ("error_registry.md", "testing/failure_inventory.md"):
        path = docs / rel
        if not path.exists():
            errors.append(f"missing docs/{rel}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"docs/{rel} is empty")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        raise SystemExit(1)
    print("audit_doctrine: all checks passed")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    audit_doctrine()
