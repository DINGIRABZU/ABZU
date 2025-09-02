"""Validate ignition module for scripts."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

__version__ = "0.2.0"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LOG_FILE = Path("logs/ignition_validation.json")

COMPONENTS = [
    ("RAZAR", "razar/boot_orchestrator.py"),
    ("Crown", "crown_router.py"),
    ("INANNA", "INANNA_AI_AGENT/inanna_ai.py"),
    ("Albedo", "albedo/state_machine.py"),
    ("Nazarick", "agents/nazarick/narrative_scribe.py"),
    ("Operator", "operator_api.py"),
]


def check_component(relative_path: str) -> Dict[str, Any]:
    """Return readiness info for ``relative_path`` without importing."""
    target = ROOT / relative_path
    if target.exists():
        return {"ready": True}
    return {"ready": False, "error": "module not found"}


async def main() -> int:
    """Validate ignition chain and persist results."""
    sequence: list[Dict[str, Any]] = []
    for name, module in COMPONENTS:
        info = check_component(module)
        info.update({"component": name, "module": module})
        sequence.append(info)

    summary = {"sequence": sequence}
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(summary, indent=2)
    LOG_FILE.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
