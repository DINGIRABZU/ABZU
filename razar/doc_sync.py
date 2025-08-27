"""Synchronize Ignition and system blueprint docs.

This utility rebuilds ``docs/Ignition.md`` and refreshes sections in
``docs/system_blueprint.md`` with the latest component status and best boot
sequence.  The sequence is pulled from ``logs/razar_boot_history.json`` and the
status mapping comes from the :class:`agents.razar.lifecycle_bus.LifecycleBus`.

Run manually with ``python -m razar.doc_sync``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

import yaml

from agents.razar.ignition_builder import build_ignition
from agents.razar.lifecycle_bus import LifecycleBus

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT_PATH = ROOT / "docs" / "system_blueprint.md"
IGNITION_PATH = ROOT / "docs" / "Ignition.md"
PRIORITY_PATH = ROOT / "docs" / "component_priorities.yaml"
HISTORY_PATH = ROOT / "logs" / "razar_boot_history.json"

COMPONENT_NAME_MAP = {
    "memory_store": "Memory Store",
    "chat_gateway": "Chat Gateway",
    "crown_llm": "CROWN LLM",
    "vision_adapter": "Vision Adapter",
    "audio_device": "Audio Device",
    "avatar": "Avatar",
    "video": "Video",
}


def _normalize(name: str) -> str:
    """Return a normalized identifier for ``name``."""

    return re.sub(r"[^a-z0-9]+", "", name.lower())


def load_best_sequence(path: Path = HISTORY_PATH) -> List[str]:
    """Return the best boot sequence if available."""

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        best = data.get("best") or {}
        if isinstance(best, dict):
            seq = best.get("sequence")
            if isinstance(seq, list):
                return [str(s) for s in seq]
    return []


def load_priorities(path: Path = PRIORITY_PATH) -> Dict[str, int]:
    """Return component priorities keyed by component name."""

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    priorities: Dict[str, int] = {}
    for name, info in data.items():
        try:
            priorities[name] = int(str(info.get("priority", "P999")).lstrip("P"))
        except Exception:  # pragma: no cover - defensive
            priorities[name] = 999
    return priorities


def update_system_blueprint(
    path: Path,
    statuses: Dict[str, str],
    sequence: List[str],
    priorities: Dict[str, int],
) -> None:
    """Update component status and boot sequence sections."""

    lines = path.read_text(encoding="utf-8").splitlines()
    status_map = {_normalize(k): v for k, v in statuses.items()}

    new_lines: List[str] = []
    heading_re = re.compile(r"^###\s+(.*)$")
    for line in lines:
        match = heading_re.match(line)
        if match:
            comp_title = match.group(1).strip()
            new_lines.append(line)
            status = status_map.get(_normalize(comp_title))
            if status:
                new_lines.append(f"- **Status:** {status}")
            continue
        if line.strip().startswith("- **Status:**"):
            continue  # existing status line
        new_lines.append(line)

    if sequence:
        start = None
        for i, line in enumerate(new_lines):
            if line.strip() == "## Staged Startup Order":
                start = i
                break
        if start is not None:
            i = start + 1
            while i < len(new_lines) and not re.match(
                r"^\d+\.\s", new_lines[i].lstrip()
            ):
                i += 1
            list_start = i
            while i < len(new_lines) and re.match(r"^\d+\.\s", new_lines[i].lstrip()):
                i += 1
            list_end = i
            boot_lines = [
                (
                    "0. RAZAR Startup Orchestrator (external, priority 0) – "
                    "see [RAZAR Agent](RAZAR_AGENT.md)"
                )
            ]
            for idx, comp in enumerate(sequence, start=1):
                title = COMPONENT_NAME_MAP.get(comp, comp.replace("_", " ").title())
                prio = priorities.get(comp, "?")
                boot_lines.append(f"{idx}. {title} (priority {prio})")
            new_lines = new_lines[:list_start] + boot_lines + new_lines[list_end:]

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def sync_docs() -> None:
    """Regenerate ignition docs and refresh the system blueprint."""

    build_ignition(BLUEPRINT_PATH, IGNITION_PATH)
    try:
        bus = LifecycleBus()
        statuses = bus.get_statuses()
    except Exception:  # pragma: no cover - runtime optional
        statuses = {}
    priorities = load_priorities()
    sequence = load_best_sequence()
    update_system_blueprint(BLUEPRINT_PATH, statuses, sequence, priorities)


def main() -> None:  # pragma: no cover - CLI entry point
    """CLI wrapper for :func:`sync_docs`."""

    sync_docs()


if __name__ == "__main__":  # pragma: no cover - module CLI
    main()
