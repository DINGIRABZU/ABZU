from __future__ import annotations

"""Validate the ignition flow by booting RAZAR and checking dependencies."""

import asyncio
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from razar.crown_handshake import CrownHandshake

__version__ = "0.1.0"

LOG_FILE = Path("logs/ignition_validation.json")
BOOT_CONFIG = Path("razar/boot_config.json")


def check_connectors() -> Dict[str, bool]:
    """Return mapping of connector id to availability."""
    statuses: Dict[str, bool] = {}
    for path in Path("connectors").glob("*_connector.py"):
        name = path.stem.replace("_connector", "")
        try:
            module = importlib.import_module(f"connectors.{path.stem}")
            getattr(module, "start_call")
            statuses[name] = True
        except Exception:  # pragma: no cover - import or attribute failures
            statuses[name] = False
    return statuses


def build_mission_brief(components: list[dict[str, Any]]) -> Path:
    """Generate mission brief file for handshake."""
    brief = {
        "priority_map": {str(c.get("name", "")): i for i, c in enumerate(components)},
        "current_status": {},
        "open_issues": [],
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    brief_path = LOG_FILE.parent / "mission_brief_validate.json"
    brief_path.write_text(json.dumps(brief))
    return brief_path


def load_components() -> list[dict[str, Any]]:
    """Load boot configuration components."""
    try:
        data = json.loads(BOOT_CONFIG.read_text())
    except Exception:  # pragma: no cover - config errors
        return []
    return data.get("components", [])


async def perform_handshake(brief_path: Path) -> Dict[str, Any]:
    """Attempt Crown handshake and return result info."""
    url = os.getenv("CROWN_WS_URL")
    if not url:
        return {"success": False, "error": "CROWN_WS_URL not set"}
    try:
        handshake = CrownHandshake(url)
        response = await handshake.perform(str(brief_path))
    except Exception as exc:  # pragma: no cover - network failures
        return {"success": False, "error": str(exc)}
    return {
        "success": True,
        "acknowledgement": response.acknowledgement,
        "capabilities": response.capabilities,
        "downtime": response.downtime,
    }


async def main() -> int:
    """Run ignition validation and persist results."""
    components = load_components()
    brief_path = build_mission_brief(components)
    handshake = await perform_handshake(brief_path)
    connectors = check_connectors()
    summary = {
        "boot_config_loaded": bool(components),
        "handshake": handshake,
        "connectors": connectors,
    }
    rendered = json.dumps(summary, indent=2)
    LOG_FILE.write_text(rendered + "\n")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
