"""Generate Ignition.md from system_blueprint.md."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


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
            if name.lower().startswith(
                meta_name.lower()
            ) or meta_name.lower().startswith(name.lower()):
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


def build_ignition(system_blueprint: Path, output: Path) -> None:
    """Build the Ignition markdown file."""

    components = parse_system_blueprint(system_blueprint)
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

    for priority in sorted(groups):
        lines.append(f"## Priority {priority}")
        lines.append("| Order | Component | Health Check | Status |")
        lines.append("| --- | --- | --- | --- |")
        for comp in sorted(groups[priority], key=lambda c: c["order"]):
            health_check = comp["health_check"] or "-"
            lines.append(f"| {comp['order']} | {comp['name']} | {health_check} | ⚠️ |")
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


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_ignition(root / "docs" / "system_blueprint.md", root / "docs" / "Ignition.md")


if __name__ == "__main__":
    main()
