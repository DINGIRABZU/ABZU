"""Update ``docs/Ignition.md`` from the component priority registry.

Components are defined in ``docs/component_priorities.yaml`` with three pieces
of metadata: ``priority`` (``P1``–``P5``), ``criticality`` and ``issue_type``.
The builder groups entries by priority and writes a Markdown table to
``docs/Ignition.md``.  Status markers (``✅``/``⚠️``/``❌``) are derived from the
last successful component recorded in ``logs/razar_state.json`` and the
quarantine registry.  The original blueprint parsing helper
:func:`parse_system_blueprint` is retained for compatibility with the boot
orchestrator.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import yaml

from . import quarantine_manager

DEFAULT_STATUS = "⚠️"


# ---------------------------------------------------------------------------
# Legacy blueprint parsing
# ---------------------------------------------------------------------------
def parse_system_blueprint(path: Path) -> List[Dict[str, object]]:
    """Extract component data from ``system_blueprint.md``.

    Returns a list of dictionaries containing the component order,
    name, priority and health check command (if available).
    """

    text = path.read_text(encoding="utf-8")

    # Collect component metadata from their sections
    heading_re = re.compile(r"^###\s+(.*)$", re.MULTILINE)
    headings = list(heading_re.finditer(text))
    meta: Dict[str, Dict[str, object]] = {}
    for idx, match in enumerate(headings):
        name = match.group(1).strip()
        start = match.end()
        end = headings[idx + 1].start() if idx + 1 < len(headings) else len(text)
        section = text[start:end]
        prio_match = re.search(r"-\s*\*\*Priority:\*\*\s*(\d+)", section)
        hc_match = re.search(r"-\s*\*\*Health Check:\*\*\s*(.+)", section)
        if prio_match:
            meta[name] = {
                "priority": int(prio_match.group(1)),
                "health_check": hc_match.group(1).strip() if hc_match else "",
            }

    # Parse the staged startup order for component ordering
    order_re = re.compile(
        r"^(\d+)\.\s+(.*?)\s*\(.*?priority\s+(\d+)\)",
        re.MULTILINE | re.IGNORECASE,
    )
    components: List[Dict[str, object]] = []
    for match in order_re.finditer(text):
        order = int(match.group(1))
        name = match.group(2).strip()
        priority = int(match.group(3))
        health_check = ""
        for meta_name, data in meta.items():
            if name.lower().startswith(meta_name.lower()) or meta_name.lower().startswith(name.lower()):
                health_check = data["health_check"]
                break
        components.append(
            {
                "order": order,
                "name": name,
                "priority": priority,
                "health_check": health_check,
            }
        )

    return components


# ---------------------------------------------------------------------------
# Registry based Ignition builder
# ---------------------------------------------------------------------------
def _load_registry(path: Path) -> List[Dict[str, object]]:
    """Return components sorted by priority from ``path``."""

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    components: List[Dict[str, object]] = []
    for name, meta in data.items():
        prio_raw = str(meta.get("priority", "P999"))
        try:
            priority = int(prio_raw.lstrip("P"))
        except Exception:  # pragma: no cover - defensive
            priority = 999
        components.append({"name": name, "priority": priority})
    components.sort(key=lambda c: (c["priority"], c["name"]))
    for idx, comp in enumerate(components, start=1):
        comp["order"] = idx
    return components


def _load_last_component(path: Path | None) -> str:
    """Return the last successfully started component from ``path``."""

    if not path or not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("last_component", ""))
    except Exception:  # pragma: no cover - defensive
        return ""


def _compute_statuses(components: List[Dict[str, object]], last: str) -> Dict[str, str]:
    """Map component names to status markers."""

    statuses: Dict[str, str] = {}
    after_last = False
    for comp in components:
        name = str(comp["name"])
        if quarantine_manager.is_quarantined(name):
            statuses[name] = "❌"
            continue
        if not last:
            statuses[name] = DEFAULT_STATUS
            continue
        if after_last:
            statuses[name] = DEFAULT_STATUS
            continue
        statuses[name] = "✅"
        if name == last:
            after_last = True
    return statuses


def build_ignition(registry: Path, output: Path, *, state: Path | None = None) -> None:
    """Build the Ignition markdown file from ``registry`` and ``state``."""

    components = _load_registry(registry)
    last = _load_last_component(state)
    statuses = _compute_statuses(components, last)

    groups: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for comp in components:
        groups[int(comp["priority"])].append(comp)

    lines = [
        "# Ignition",
        "",
        (
            "RAZAR coordinates system boot and records runtime health. "
            "Components are grouped by priority so operators can track "
            "startup order and service status."
        ),
        "",
    ]

    orch_status = "✅" if last else DEFAULT_STATUS
    lines.extend(
        [
            "## Priority 0",
            "| Order | Component | Health Check | Status |",
            "| --- | --- | --- | --- |",
            (
                "| 0 | RAZAR Startup Orchestrator | "
                "Confirm the environment hash and orchestrator heartbeat. | "
                f"{orch_status} |"
            ),
            "",
        ]
    )

    for priority in sorted(groups):
        lines.append(f"## Priority {priority}")
        lines.append("| Order | Component | Health Check | Status |")
        lines.append("| --- | --- | --- | --- |")
        for comp in groups[priority]:
            overrides = {"crown_llm": "CROWN LLM"}
            name = overrides.get(
                comp["name"], comp["name"].replace("_", " ").title()
            )
            status = statuses.get(comp["name"], DEFAULT_STATUS)
            lines.append(f"| {comp['order']} | {name} | - | {status} |")
        lines.append("")

    lines.extend(
        [
            "## Regeneration",
            (
                "RAZAR monitors component events and rewrites this file whenever a "
                "priority or health state changes. Status markers update to:"
            ),
            "",
            "- ✅ healthy",
            "- ⚠️ starting or degraded",
            "- ❌ offline",
            "",
            "This keeps the ignition sequence in version control so operators can "
            "audit boot cycles.",
            "",
        ]
    )

    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:  # pragma: no cover - CLI helper
    root = Path(__file__).resolve().parents[2]
    build_ignition(
        root / "docs" / "component_priorities.yaml",
        root / "docs" / "Ignition.md",
        state=root / "logs" / "razar_state.json",
    )


if __name__ == "__main__":  # pragma: no cover - module CLI
    main()

