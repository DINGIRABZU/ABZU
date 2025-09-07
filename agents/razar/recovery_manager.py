"""Recovery manager using ZeroMQ for error handling.

The recovery protocol is initiated when a running component reports an
unrecoverable error. The component connects to the configured ZeroMQ endpoint
and sends a JSON message containing the module name and any serialisable state.
RAZAR takes ownership of the recovery process:

1. Pause the system via the lifecycle bus.
2. Save the provided state to disk.
3. Apply a patch through the remote code agent.
4. Restart the affected module.
5. Restore the saved state after restart and resume the system.

A confirmation response is sent back to the component once recovery completes.
"""

from __future__ import annotations

__version__ = "0.2.2"

import json
import logging
import asyncio
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import zmq
except Exception:  # pragma: no cover - optional dependency
    zmq = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from .lifecycle_bus import LifecycleBus
    from .code_repair import repair_module
except Exception:  # pragma: no cover - optional dependency
    LifecycleBus = None  # type: ignore
    repair_module = None  # type: ignore

from . import lifecycle_bus


logger = logging.getLogger(__name__)


class RecoveryManager:
    """Coordinate recovery actions for failed modules."""

    def __init__(
        self,
        endpoint: str,
        *,
        state_dir: Path | None = None,
        bus: LifecycleBus | None = None,
    ) -> None:
        if zmq is None:  # pragma: no cover - dependency check
            raise RuntimeError("pyzmq is required for RecoveryManager")
        if (
            bus is None and LifecycleBus is None
        ):  # pragma: no cover - optional dependency
            raise RuntimeError("LifecycleBus is required for RecoveryManager")
        self.endpoint = endpoint
        self.state_dir = state_dir or Path("recovery_state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.bus = bus or LifecycleBus()  # type: ignore[call-arg]
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(endpoint)

    # ------------------------------------------------------------------
    def serve(self) -> None:
        """Listen for error reports and trigger recovery."""

        while True:
            message = self.socket.recv_json()
            module = str(message.get("module", "unknown"))
            state = message.get("state", {})
            logger.warning("Unrecoverable error reported from %s", module)
            self.recover(module, state)
            self.socket.send_json({"module": module, "status": "recovered"})

    # ------------------------------------------------------------------
    def recover(self, module: str, state: Dict[str, Any]) -> None:
        """Run the full recovery procedure for ``module``."""
        # Broadcast the component failure before beginning recovery so that
        # auxiliary services can react (e.g. Nazarick remediation agents).
        self.bus.report_issue(module, "component_down")

        self.pause_system()
        self.save_state(module, state)
        self.apply_fixes(module)
        self.restart_module(module)
        confirmed = self.wait_for_resuscitator(module)
        if confirmed:
            self.bus.publish_status(module, "healthy")
        self.restore_state(module, state)
        self.resume_system()

    # ------------------------------------------------------------------
    def save_state(self, module: str, state: Dict[str, Any]) -> None:
        """Persist the provided ``state`` for ``module``."""

        path = self.state_dir / f"{module}.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        logger.info("State for %s saved to %s", module, path)

    # ------------------------------------------------------------------
    def pause_system(self) -> None:
        """Broadcast a pause instruction to all components."""

        self.bus.send_control("system", "pause")

    # ------------------------------------------------------------------
    def resume_system(self) -> None:
        """Broadcast a resume instruction to all components."""

        self.bus.send_control("system", "resume")

    # ------------------------------------------------------------------
    def apply_fixes(self, module: str) -> None:  # pragma: no cover - placeholder
        """Apply corrective actions for ``module`` using the remote agent."""

        if repair_module is None:  # pragma: no cover - defensive
            logger.warning("repair_module unavailable; skipping patch step")
            return
        module_path = Path(f"{module}.py")
        tests = [Path("tests") / f"test_{module}.py"]
        logger.info("Requesting patch for %s", module_path)
        repair_module(module_path, tests, "unrecoverable error")

    # ------------------------------------------------------------------
    def restart_module(self, module: str) -> None:
        """Restart the failed ``module`` via the lifecycle bus."""

        logger.info("Restarting module %s", module)
        self.bus.send_control(module, "restart")

    # ------------------------------------------------------------------
    def wait_for_resuscitator(self, module: str, timeout: float = 30.0) -> bool:
        """Block until a resuscitator confirms recovery for ``module``."""

        async def _wait() -> bool:
            async for event in lifecycle_bus.subscribe():
                if (
                    event.get("event") == "agent_resuscitated"
                    and event.get("agent") == module
                ):
                    return True
            return False

        try:
            return asyncio.run(asyncio.wait_for(_wait(), timeout))
        except asyncio.TimeoutError:
            logger.warning(
                "Timed out waiting for resuscitator confirmation for %s", module
            )
            return False

    # ------------------------------------------------------------------
    def restore_state(self, module: str, state: Dict[str, Any]) -> None:
        """Restore ``state`` to ``module`` after restart."""

        logger.info("Restoring state for %s", module)
        path = self.state_dir / f"{module}.json"
        if not path.exists():  # pragma: no cover - defensive
            return
        self.bus.send_control(module, "restore")

    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close ZeroMQ resources."""

        self.socket.close(0)
        self.context.term()
