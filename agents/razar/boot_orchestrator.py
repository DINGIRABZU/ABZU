"""Boot orchestrator for the RAZAR agent.

The orchestrator derives the component startup order from
``docs/system_blueprint.md`` and regenerates ``docs/Ignition.md`` with
status markers. Components are launched sequentially and progress is
persisted to ``logs/razar_state.json`` so subsequent runs can resume from
the last successful component.
"""

from __future__ import annotations

import argparse
import json
import logging
import shlex
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - dependency is handled in tests
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("pyyaml is required for the boot orchestrator") from exc

from . import health_checks
from .ignition_builder import DEFAULT_STATUS, parse_system_blueprint

LOGGER = logging.getLogger(__name__)


class BootOrchestrator:
    """Coordinate staged startup for core ABZU services."""

    def __init__(
        self,
        *,
        blueprint: Path | None = None,
        config: Path | None = None,
        ignition: Path | None = None,
        state: Path | None = None,
    ) -> None:
        root = Path(__file__).resolve().parents[2]
        self.blueprint_path = blueprint or root / "docs" / "system_blueprint.md"
        self.config_path = config or root / "config" / "razar_config.yaml"
        self.ignition_path = ignition or root / "docs" / "Ignition.md"
        self.state_path = state or root / "logs" / "razar_state.json"

        self.components = parse_system_blueprint(self.blueprint_path)
        self.statuses: Dict[str, str] = {
            str(comp["name"]): DEFAULT_STATUS for comp in self.components
        }

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def load_state(self) -> str:
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return str(data.get("last_component", ""))
            except json.JSONDecodeError:
                return ""
        return ""

    def save_state(self, name: str) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps({"last_component": name}), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # Ignition file handling
    # ------------------------------------------------------------------
    def _render_ignition(self) -> str:
        groups: Dict[int, List[Dict[str, object]]] = defaultdict(list)
        for comp in self.components:
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
                status = self.statuses.get(str(comp["name"]), DEFAULT_STATUS)
                lines.append(
                    f"| {comp['order']} | {comp['name']} | {health_check} | {status} |"
                )
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

        return "\n".join(lines)

    def write_ignition(self) -> None:
        self.ignition_path.write_text(self._render_ignition(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Component launching
    # ------------------------------------------------------------------
    def _load_commands(self) -> Dict[str, str]:
        if not self.config_path.exists():
            return {}
        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        comps = data.get("components", [])
        return {str(c.get("name")): str(c.get("command", "")) for c in comps}

    def _launch(self, comp: Dict[str, object], commands: Dict[str, str]) -> None:
        name = str(comp.get("name"))
        cmd = commands.get(name) or f"echo launching {name}"
        LOGGER.info("Starting component %s", name)
        result = subprocess.run(
            shlex.split(cmd) if isinstance(cmd, str) else cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode != 0:
            LOGGER.error("Component %s failed: %s", name, result.stdout)
            self.statuses[name] = "❌"
            self.write_ignition()
            raise RuntimeError(f"{name} failed to start")

        if not health_checks.run(name):
            LOGGER.error("Health check failed for %s", name)
            self.statuses[name] = "❌"
            self.write_ignition()
            raise RuntimeError(f"Health check failed for {name}")

        self.statuses[name] = "✅"
        self.save_state(name)
        self.write_ignition()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> bool:
        """Execute the staged startup sequence."""

        self.write_ignition()
        commands = self._load_commands()
        last = self.load_state()

        start_index = 0
        if last:
            for idx, comp in enumerate(self.components):
                if comp.get("name") == last:
                    start_index = idx + 1
                    break
            if start_index:
                LOGGER.info("Resuming after component %s", last)

        for comp in self.components[start_index:]:
            try:
                self._launch(comp, commands)
            except RuntimeError:
                return False

        LOGGER.info("Boot sequence complete")
        return True


def main() -> None:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="Run the RAZAR boot orchestrator")
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--blueprint", type=Path, default=root / "docs" / "system_blueprint.md"
    )
    parser.add_argument(
        "--config", type=Path, default=root / "config" / "razar_config.yaml"
    )
    parser.add_argument(
        "--ignition", type=Path, default=root / "docs" / "Ignition.md"
    )
    parser.add_argument("--state", type=Path, default=root / "logs" / "razar_state.json")
    args = parser.parse_args()

    orchestrator = BootOrchestrator(
        blueprint=args.blueprint,
        config=args.config,
        ignition=args.ignition,
        state=args.state,
    )
    success = orchestrator.run()
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()

