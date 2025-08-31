"""RAZAR runtime manager.

This module ensures a Python virtual environment exists and uses it to
sequentially start system components based on their priority. Component
dependencies are resolved from ``razar_env.yaml`` and installed into the
managed environment.  Every successful component launch is recorded in
``logs/razar_state.json`` so the manager can resume from the most recent
healthy component after a failure.  Components that fail their startup command
or a subsequent health check are quarantined via ``quarantine_manager``.
"""

from __future__ import annotations

__version__ = "0.2.2"

import logging
import os
import subprocess
import shlex
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import venv
from . import checkpoint_manager, health_checks, quarantine_manager

# Re-export primary entry points for simpler imports
__all__ = ["RuntimeManager", "main"]

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependencies handled by tests
    raise RuntimeError("pyyaml is required to load razar configuration") from exc


logger = logging.getLogger(__name__)


class RuntimeManager:
    """Start components defined in a configuration file."""

    def __init__(
        self,
        config_path: Path,
        *,
        state_path: Path | None = None,
        venv_path: Path | None = None,
        env_path: Path | None = None,
    ) -> None:
        self.config_path = config_path
        self.state_path = state_path or Path("logs/razar_state.json")
        self.venv_path = venv_path or config_path.parent / ".razar_venv"
        # ``razar_env.yaml`` lives at the repository root and lists dependencies
        # for each component layer.  Allow ``env_path`` to be overridden for
        # tests but default to the project-level file.
        self.env_path = (
            env_path or Path(__file__).resolve().parents[2] / "razar_env.yaml"
        )

    # ------------------------------------------------------------------
    # Virtual environment handling
    # ------------------------------------------------------------------
    def ensure_venv(self, dependencies: Sequence[str] | None = None) -> None:
        """Create a virtual environment and install ``dependencies``.

        Parameters
        ----------
        dependencies:
            An optional sequence of package specifications understood by
            ``pip``. They are installed into the managed virtual environment in
            the order provided. Installation is skipped if the sequence is
            empty.
        """

        if not self.venv_path.exists():
            logger.info("Creating virtual environment at %s", self.venv_path)
            builder = venv.EnvBuilder(with_pip=True)
            builder.create(self.venv_path)
        else:
            logger.info("Using existing virtual environment at %s", self.venv_path)

        if dependencies:
            bin_dir = "Scripts" if os.name == "nt" else "bin"
            pip_path = self.venv_path / bin_dir / "pip"
            cmd = [str(pip_path), "install", *dependencies]
            logger.info("Installing dependencies: %s", " ".join(dependencies))
            # Best effort install; failures propagate to caller
            subprocess.run(cmd, check=True)

    # ------------------------------------------------------------------
    # State persistence helpers
    # ------------------------------------------------------------------
    def load_state(self) -> str:
        """Return the name of the last successful component."""

        return checkpoint_manager.load_checkpoint(self.state_path)

    def save_state(self, name: str) -> None:
        checkpoint_manager.save_checkpoint(name, self.state_path)

    # ------------------------------------------------------------------
    # Component execution
    # ------------------------------------------------------------------
    def _env(self) -> Dict[str, str]:
        env = os.environ.copy()
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        env["VIRTUAL_ENV"] = str(self.venv_path)
        env["PATH"] = str(self.venv_path / bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def _load_config(self) -> Dict[str, object]:
        """Load and return the full YAML configuration."""

        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def _env_dependencies(self, components: Sequence[Dict[str, object]]) -> List[str]:
        """Return dependency list for ``components`` from ``razar_env.yaml``."""

        if not self.env_path.exists():
            return []

        raw = yaml.safe_load(self.env_path.read_text(encoding="utf-8")) or {}
        layers = raw.get("layers", {})
        deps: List[str] = []
        for comp in components:
            name = comp.get("name")
            if name in layers:
                deps.extend(layers[name])
        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for dep in deps:
            if dep not in seen:
                seen.add(dep)
                unique.append(dep)
        return unique

    def _load_components(self, config: Dict[str, object]) -> List[Dict[str, object]]:
        components = config.get("components", [])
        return sorted(components, key=lambda c: int(c.get("priority", 0)))

    def _starting_index(
        self, components: Iterable[Dict[str, object]], last: str
    ) -> int:
        if not last:
            return 0
        for idx, comp in enumerate(components):
            if comp.get("name") == last:
                return idx + 1
        return 0

    def run(self) -> bool:
        """Run components in order. Returns ``True`` if all succeed."""

        config = self._load_config()
        components = self._load_components(config)
        # Install dependencies declared for the target components in
        # ``razar_env.yaml``.  Components without entries require no additional
        # packages which keeps test environments light-weight.
        dependencies = self._env_dependencies(components)
        self.ensure_venv(dependencies)
        last = self.load_state()
        start = self._starting_index(components, last)
        env = self._env()

        if last:
            logger.info("Resuming after component %s", last)

        for comp in components[start:]:
            name = comp.get("name", "<unknown>")
            if quarantine_manager.is_quarantined(str(name)):
                logger.warning("Skipping quarantined component %s", name)
                continue
            command = comp.get("command", "")
            logger.info("Starting component %s", name)
            result = subprocess.run(
                shlex.split(command) if isinstance(command, str) else command,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.config_path.parent),
            )
            if result.returncode != 0:
                logger.error(
                    "Component %s failed with code %s\n%s",
                    name,
                    result.returncode,
                    result.stdout,
                )
                reason = f"exit code {result.returncode}"
                quarantine_manager.quarantine_component(
                    comp,
                    reason,
                    diagnostics={"output": result.stdout},
                )
                module_path = (
                    comp.get("module_path") or comp.get("path") or comp.get("module")
                )
                if module_path:
                    try:
                        quarantine_manager.quarantine_module(module_path, reason)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.error(
                            "Module quarantine failed for %s: %s", module_path, exc
                        )
                return False

            if not health_checks.run(str(name)):
                logger.error("Health check failed for %s", name)
                reason = "health check failed"
                quarantine_manager.quarantine_component(comp, reason)
                module_path = (
                    comp.get("module_path") or comp.get("path") or comp.get("module")
                )
                if module_path:
                    try:
                        quarantine_manager.quarantine_module(module_path, reason)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.error(
                            "Module quarantine failed for %s: %s", module_path, exc
                        )
                return False

            logger.info("Component %s started successfully", name)
            last = str(name)
            self.save_state(last)

        logger.info("Boot sequence complete. Last component: %s", last)
        return True


def main() -> None:  # pragma: no cover - CLI helper
    import argparse

    parser = argparse.ArgumentParser(description="Run components via RAZAR")
    parser.add_argument("config", type=Path, help="Path to razar_config.yaml")
    args = parser.parse_args()

    manager = RuntimeManager(args.config)
    success = manager.run()
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":  # pragma: no cover
    main()
