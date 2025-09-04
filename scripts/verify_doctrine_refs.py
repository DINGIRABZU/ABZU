from __future__ import annotations

"""Verify key documentation references.

This script enforces three documentation invariants:

* ``docs/The_Absolute_Protocol.md`` mentions the rule to read
  ``blueprint_spine.md`` three times.
* ``docs/INDEX.md`` contains entries for ``The_Absolute_Protocol.md`` and
  ``blueprint_spine.md``.
* ``docs/error_registry.md`` and ``docs/testing/failure_inventory.md`` exist.

The script exits with a non-zero status and prints the failing checks when any
invariant is violated. It is intended for use as a pre-commit hook.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

BLUEPRINT_RULE = "read [blueprint_spine.md](blueprint_spine.md) three times"


def verify_doctrine_refs(root: Path | None = None) -> None:
    """Validate documentation references under *root* (defaults to repo root)."""
    base = Path(root) if root else ROOT
    docs = base / "docs"
    errors: list[str] = []

    # Check Absolute Protocol rule
    protocol_path = docs / "The_Absolute_Protocol.md"
    if not protocol_path.exists():
        errors.append(f"missing {protocol_path}")
    else:
        text = protocol_path.read_text(encoding="utf-8").lower()
        if BLUEPRINT_RULE.lower() not in text:
            errors.append(
                "The_Absolute_Protocol.md missing 'read blueprint_spine.md three times' rule"
            )

    # Ensure INDEX includes protocol and blueprint entries
    index_path = docs / "INDEX.md"
    if not index_path.exists():
        errors.append("missing docs/INDEX.md")
    else:
        index_text = index_path.read_text(encoding="utf-8")
        for name in ("The_Absolute_Protocol.md", "blueprint_spine.md"):
            if name not in index_text:
                errors.append(f"{name} not listed in INDEX.md")

    # Required supporting docs
    for rel in ("error_registry.md", "testing/failure_inventory.md"):
        if not (docs / rel).exists():
            errors.append(f"missing docs/{rel}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        raise SystemExit(1)
    print("verify_doctrine_refs: all checks passed")


if __name__ == "__main__":  # pragma: no cover - CLI entry
    verify_doctrine_refs()
