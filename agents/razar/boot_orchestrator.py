"""Boot orchestrator for the RAZAR agent.

The orchestrator derives the component startup order from
``docs/system_blueprint.md`` and regenerates ``docs/Ignition.md`` with
status markers. Components are launched sequentially and progress is
persisted to ``logs/razar_state.json`` so subsequent runs can resume from
the last successful component.
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import asyncio
import json
import logging
import os
import shlex
import subprocess
import time
import urllib.request
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List

try:  # pragma: no cover - dependency is handled in tests
    import yaml
except Exception as exc:  # pragma: no cover
    raise RuntimeError("pyyaml is required for the boot orchestrator") from exc

from . import (
    ai_invoker,
    code_repair,
    health_checks,
    mission_logger,
    quarantine_manager,
)
from .ignition_builder import DEFAULT_STATUS, parse_system_blueprint
from razar.crown_handshake import CrownHandshake, CrownResponse

LOGGER = logging.getLogger(__name__)

MAX_MISSION_BRIEFS = 20


class BootOrchestrator:
    """Coordinate staged startup for core ABZU services."""

    def __init__(
        self,
        *,
        blueprint: Path | None = None,
        config: Path | None = None,
        ignition: Path | None = None,
        state: Path | None = None,
        retries: int = 3,
        enable_ai_handover: bool | None = None,
    ) -> None:
        """Initialize orchestrator paths and configuration."""
        root = Path(__file__).resolve().parents[2]
        self.blueprint_path = blueprint or root / "docs" / "system_blueprint.md"
        self.config_path = config or root / "config" / "razar_config.yaml"
        self.ignition_path = ignition or root / "docs" / "Ignition.md"
        self.state_path = state or root / "logs" / "razar_state.json"

        self.components = parse_system_blueprint(self.blueprint_path)
        self.statuses: Dict[str, str] = {
            str(comp["name"]): DEFAULT_STATUS for comp in self.components
        }
        self.retries = retries
        self.enable_ai_handover = (
            bool(enable_ai_handover) if enable_ai_handover is not None else False
        )

    # ------------------------------------------------------------------
    # Primordials launch
    # ------------------------------------------------------------------
    def _wait_for_primordials(self, url: str, retries: int = 30) -> None:
        """Poll ``url`` until the Primordials service reports healthy."""
        health_url = f"{url.rstrip('/')}/health"
        for _ in range(retries):
            try:
                with urllib.request.urlopen(health_url) as resp:  # pragma: no cover
                    if resp.status == 200:
                        return
            except Exception:  # pragma: no cover - network may be unavailable
                time.sleep(1)
        raise RuntimeError("Primordials service failed health check")

    def _start_primordials(self) -> None:
        """Launch the Primordials container and wait for readiness."""
        url = os.environ.get("PRIMORDIALS_API_URL", "http://localhost:8080")
        LOGGER.info("Primordials API URL: %s", url)
        subprocess.run(["docker", "compose", "up", "-d", "primordials"], check=False)
        self._wait_for_primordials(url)

    # ------------------------------------------------------------------
    # Crown handshake
    # ------------------------------------------------------------------
    def _persist_handshake(self, response: CrownResponse | None) -> None:
        """Store handshake ``response`` details in the state file."""
        data: Dict[str, object] = {}
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        if response is not None:
            data["capabilities"] = response.capabilities
            data["downtime"] = response.downtime
            data["handshake"] = asdict(response)
        else:
            data.setdefault("capabilities", [])
            data.setdefault("downtime", {})
            data.setdefault(
                "handshake",
                {"acknowledgement": "", "capabilities": [], "downtime": {}},
            )
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(data), encoding="utf-8")

    def _perform_handshake(self) -> CrownResponse:
        """Send mission brief to CROWN and return the raw response."""
        brief = {
            "priority_map": {
                str(c["name"]): int(c["priority"]) for c in self.components
            },
            "current_status": self.statuses,
            "open_issues": [],
        }
        archive_dir = self.state_path.parent / "mission_briefs"
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        brief_path = archive_dir / f"{timestamp}.json"
        brief_path.write_text(json.dumps(brief), encoding="utf-8")
        response_path = archive_dir / f"{timestamp}_response.json"

        try:
            url = os.environ["CROWN_WS_URL"]
            handshake = CrownHandshake(url)
            response = asyncio.run(handshake.perform(str(brief_path)))
            details = json.dumps(
                {"capabilities": response.capabilities, "downtime": response.downtime}
            )
            status = "success"
        except Exception as exc:  # pragma: no cover - handshake must succeed
            LOGGER.exception("CROWN handshake failed")
            mission_logger.log_event("handshake", "crown", "failure", str(exc))
            response_path.write_text("{}", encoding="utf-8")
            raise RuntimeError("CROWN handshake failed") from exc

        mission_logger.log_event("handshake", "crown", status, details)
        LOGGER.info(
            "Handshake result: capabilities=%s downtime=%s",
            response.capabilities,
            response.downtime,
        )
        response_path.write_text(json.dumps(asdict(response)), encoding="utf-8")
        self._rotate_mission_briefs(archive_dir)
        return response

    def _rotate_mission_briefs(
        self, archive_dir: Path, limit: int = MAX_MISSION_BRIEFS
    ) -> None:
        """Remove oldest mission brief/response pairs beyond ``limit``."""
        briefs = sorted(
            [p for p in archive_dir.glob("*.json") if "_response" not in p.name],
            key=lambda p: p.stat().st_mtime,
        )
        excess = len(briefs) - limit
        for old in briefs[:excess]:
            response_file = archive_dir / f"{old.stem}_response.json"
            if old.exists():
                old.unlink()
            if response_file.exists():
                response_file.unlink()

    def _ensure_glm4v(self, capabilities: List[str]) -> None:
        """Ensure the GLM‑4.1V model is available, launching it if required."""
        normalized = {c.replace("-", "").upper() for c in capabilities}
        present = any(c.startswith("GLM4V") for c in normalized)

        data: Dict[str, object] = {}
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}

        data["glm4v_present"] = present

        if present:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(data), encoding="utf-8")
            return

        script = self.state_path.parents[1] / "crown_model_launcher.sh"
        LOGGER.info("Launching GLM-4.1V via %s", script)
        subprocess.run(["bash", str(script)], check=False)
        mission_logger.log_event("model_launch", "GLM-4.1V", "triggered")
        launches = data.get("launched_models", [])
        if "GLM-4.1V" not in launches:
            launches.append("GLM-4.1V")
        data["launched_models"] = launches
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(data), encoding="utf-8")

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------
    def load_state(self) -> str:
        """Return the last successfully launched component."""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return str(data.get("last_component", ""))
            except json.JSONDecodeError:
                return ""
        return ""

    def save_state(self, name: str) -> None:
        """Persist ``name`` as the last successful component."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        data: Dict[str, object] = {}
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        data["last_component"] = name
        self.state_path.write_text(json.dumps(data), encoding="utf-8")

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
        """Regenerate the ignition summary file."""
        self.ignition_path.write_text(self._render_ignition(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Component launching
    # ------------------------------------------------------------------
    def _ai_handover(self, name: str, error: str) -> None:
        """Invoke the remote agent for repair suggestions and apply patches."""
        try:
            suggestion = ai_invoker.handover(
                patch_context={"component": name, "error": error}
            )
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("AI handover invocation failed for %s", name)
            return
        if not suggestion:
            return
        patches = suggestion if isinstance(suggestion, list) else [suggestion]
        for patch in patches:
            module = patch.get("module")
            if not module:
                continue
            tests = [Path(t) for t in patch.get("tests", [])]
            err = patch.get("error", error)
            try:
                code_repair.repair_module(Path(module), tests, err)
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Failed to apply patch for %s", module)
        # Reload commands in case patches updated configuration
        self._load_commands()

    def _load_commands(self) -> Dict[str, str]:
        """Return mapping of component names to launch commands."""
        if not self.config_path.exists():
            self.enable_ai_handover = False
            return {}
        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        self.enable_ai_handover = bool(
            data.get("enable_ai_handover", self.enable_ai_handover)
        )
        comps = data.get("components", [])
        return {str(c.get("name")): str(c.get("command", "")) for c in comps}

    def _launch(
        self,
        comp: Dict[str, object],
        commands: Dict[str, str],
        *,
        handover_attempted: bool = False,
    ) -> None:
        name = str(comp.get("name"))
        cmd = commands.get(name) or f"echo launching {name}"

        for attempt in range(1, self.retries + 2):
            LOGGER.info("Starting component %s (attempt %s)", name, attempt)
            result = subprocess.run(
                shlex.split(cmd) if isinstance(cmd, str) else cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if result.returncode == 0 and health_checks.run(name):
                self.statuses[name] = "✅"
                self.save_state(name)
                self.write_ignition()
                return

            LOGGER.error("Component %s failed: %s", name, result.stdout)
            if attempt > self.retries:
                if self.enable_ai_handover and not handover_attempted:
                    self._ai_handover(name, result.stdout)
                    # Retry with fresh commands once after handover
                    new_commands = self._load_commands()
                    self._launch(comp, new_commands, handover_attempted=True)
                    return
                quarantine_manager.quarantine_component(
                    comp,
                    "launch failure",
                    diagnostics={"output": result.stdout},
                )
                self.statuses[name] = "❌"
                self.write_ignition()
                raise RuntimeError(f"{name} failed to start")
            time.sleep(1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> bool:
        """Execute the staged startup sequence."""
        self.write_ignition()
        self._start_primordials()
        response = self._perform_handshake()
        self._persist_handshake(response)
        capabilities = response.capabilities if response else []
        LOGGER.info("CROWN capabilities: %s", capabilities)
        self._ensure_glm4v(capabilities)
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
            name = str(comp.get("name"))
            if quarantine_manager.is_quarantined(name):
                LOGGER.info("Skipping quarantined component %s", name)
                self.statuses[name] = "❌"
                self.write_ignition()
                continue
            if name not in commands or not commands.get(name):
                LOGGER.error("Missing command for component %s", name)
                if self.enable_ai_handover:
                    self._ai_handover(name, "missing command")
                    commands = self._load_commands()
                if name not in commands or not commands.get(name):
                    self.statuses[name] = "❌"
                    self.write_ignition()
                    return False
            try:
                self._launch(comp, commands)
            except RuntimeError:
                return False
            commands = self._load_commands()

        LOGGER.info("Boot sequence complete")
        return True


def main() -> None:  # pragma: no cover - CLI helper
    """Command-line entry point for the boot orchestrator."""
    parser = argparse.ArgumentParser(description="Run the RAZAR boot orchestrator")
    root = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--blueprint", type=Path, default=root / "docs" / "system_blueprint.md"
    )
    parser.add_argument(
        "--config", type=Path, default=root / "config" / "razar_config.yaml"
    )
    parser.add_argument("--ignition", type=Path, default=root / "docs" / "Ignition.md")
    parser.add_argument(
        "--state", type=Path, default=root / "logs" / "razar_state.json"
    )
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    orchestrator = BootOrchestrator(
        blueprint=args.blueprint,
        config=args.config,
        ignition=args.ignition,
        state=args.state,
        retries=args.retries,
    )
    success = orchestrator.run()
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
