"""RAZAR runtime manager.

This module ensures a Python virtual environment exists and uses it to
sequentially start system components based on their priority. Progress is
logged and the last successfully started component is cached so the manager can
resume from that point after a failure.
"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List
import venv

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
    ) -> None:
        self.config_path = config_path
        self.state_path = state_path or config_path.with_suffix(".state")
        self.venv_path = venv_path or config_path.parent / ".razar_venv"
    # ------------------------------------------------------------------
    # Virtual environment handling
    # ------------------------------------------------------------------
    def ensure_venv(self) -> None:
        """Create a virtual environment if missing."""

        if not self.venv_path.exists():
            logger.info("Creating virtual environment at %s", self.venv_path)
            builder = venv.EnvBuilder(with_pip=False)
            builder.create(self.venv_path)
        else:
            logger.info("Using existing virtual environment at %s", self.venv_path)

    # ------------------------------------------------------------------
    # State persistence helpers
    # ------------------------------------------------------------------
    def load_state(self) -> str:
        """Return the name of the last successful component."""

        if self.state_path.exists():
            return self.state_path.read_text(encoding="utf-8").strip()
        return ""

    def save_state(self, name: str) -> None:
        self.state_path.write_text(name, encoding="utf-8")

    # ------------------------------------------------------------------
    # Component execution
    # ------------------------------------------------------------------
    def _env(self) -> Dict[str, str]:
        env = os.environ.copy()
        bin_dir = "Scripts" if os.name == "nt" else "bin"
        env["VIRTUAL_ENV"] = str(self.venv_path)
        env["PATH"] = str(self.venv_path / bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def _load_components(self) -> List[Dict[str, object]]:
        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        components = data.get("components", []) if isinstance(data, dict) else []
        return sorted(components, key=lambda c: int(c.get("priority", 0)))

    def _starting_index(self, components: Iterable[Dict[str, object]]) -> int:
        last = self.load_state()
        if not last:
            return 0
        for idx, comp in enumerate(components):
            if comp.get("name") == last:
                return idx + 1
        return 0

    def run(self) -> bool:
        """Run components in order. Returns ``True`` if all succeed."""

        self.ensure_venv()
        components = self._load_components()
        start = self._starting_index(components)
        env = self._env()

        for comp in components[start:]:
            name = comp.get("name", "<unknown>")
            command = comp.get("command", "")
            logger.info("Starting component %s", name)
            result = subprocess.run(
                command,
                shell=True,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.config_path.parent),
            )
            if result.returncode == 0:
                logger.info("Component %s started successfully", name)
                self.save_state(str(name))
                continue

            logger.error(
                "Component %s failed with code %s\n%s",
                name,
                result.returncode,
                result.stdout,
            )
            return False

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
