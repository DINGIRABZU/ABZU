"""Ensure system_blueprint.md references all Rust crates."""

import sys
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]
CARGO_TOML = ROOT / "Cargo.toml"
SYSTEM_BLUEPRINT = ROOT / "docs" / "system_blueprint.md"


def load_crates() -> list[str]:
    cargo = tomllib.loads(CARGO_TOML.read_text(encoding="utf-8"))
    return cargo.get("workspace", {}).get("members", [])


def main() -> int:
    crates = load_crates()
    text = SYSTEM_BLUEPRINT.read_text(encoding="utf-8")
    missing = [c for c in crates if c not in text]
    if missing:
        print(f"missing {', '.join(missing)} in system_blueprint.md", file=sys.stderr)
        return 1
    print("verify_blueprint_refs: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
