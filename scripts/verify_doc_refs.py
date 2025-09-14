from __future__ import annotations
from __future__ import annotations
from __future__ import annotations

"""Ensure feature parity and migration crosswalk reference all workspace crates."""

import sys
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CARGO_TOML = ROOT / "Cargo.toml"
FEATURE_PARITY = ROOT / "docs" / "feature_parity.md"
MIGRATION_CROSSWALK = ROOT / "docs" / "migration_crosswalk.md"


def load_crates() -> list[str]:
    cargo = tomllib.loads(CARGO_TOML.read_text(encoding="utf-8"))
    return cargo.get("workspace", {}).get("members", [])


def check_doc(path: Path, crates: list[str]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return [c for c in crates if c not in text]


def main() -> int:
    crates = load_crates()
    missing = {
        "feature_parity.md": check_doc(FEATURE_PARITY, crates),
        "migration_crosswalk.md": check_doc(MIGRATION_CROSSWALK, crates),
    }
    failures = {k: v for k, v in missing.items() if v}
    if failures:
        for doc, names in failures.items():
            print(f"missing {', '.join(names)} in {doc}", file=sys.stderr)
        return 1
    print("verify_doc_refs: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
