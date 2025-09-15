from __future__ import annotations

from pathlib import Path
import sys
import tomllib

PATH = Path(__file__).resolve().parents[1] / "NEOABZU" / "pyproject.toml"


def main() -> int:
    data = tomllib.loads(PATH.read_text(encoding="utf-8"))
    bindings = data.get("tool", {}).get("maturin", {}).get("bindings")
    if bindings != "pyo3":
        print(
            "NEOABZU/pyproject.toml missing tool.maturin.bindings = 'pyo3'",
            file=sys.stderr,
        )
        return 1
    print("verify_pyo3_exposure: bindings validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
