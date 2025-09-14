from __future__ import annotations

"""Ensure Rust workspace crates are documented and exposed to Python."""

# This helper prevents new Rust crates from being added without
# documenting them or exposing Python bindings.
import sys
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]

# Paths
CARGO_TOML = ROOT / "Cargo.toml"
BLUEPRINT = ROOT / "docs" / "blueprint_spine.md"
DOCTRINE = ROOT / "docs" / "doctrine_index.md"
PYPROJECT = ROOT / "NEOABZU" / "pyproject.toml"


def load_crates() -> list[str]:
    cargo = tomllib.loads(CARGO_TOML.read_text(encoding="utf-8"))
    return cargo.get("workspace", {}).get("members", [])


def check_blueprint(crates: list[str]) -> list[str]:
    text = BLUEPRINT.read_text(encoding="utf-8")
    return [c for c in crates if c not in text]


def check_doctrine(crates: list[str]) -> list[str]:
    text = DOCTRINE.read_text(encoding="utf-8")
    return [c for c in crates if c not in text]


def check_pyproject(crates: list[str]) -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    targets = {
        t.get("path")
        for t in data.get("tool", {}).get("maturin", {}).get("targets", [])
    }
    return [c for c in crates if c not in targets]


def main() -> int:
    crates = load_crates()
    missing = {
        "blueprint_spine.md": check_blueprint(crates),
        "doctrine_index.md": check_doctrine(crates),
        "NEOABZU/pyproject.toml targets": check_pyproject(crates),
    }
    failures = {k: v for k, v in missing.items() if v}
    if failures:
        for target, names in failures.items():
            print(f"missing {', '.join(names)} in {target}", file=sys.stderr)
        return 1
    print("verify_crate_refs: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
