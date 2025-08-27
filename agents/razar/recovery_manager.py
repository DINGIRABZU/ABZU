from __future__ import annotations

"""Recovery manager using ZeroMQ for error handling.

The recovery protocol is initiated when a running component reports an
unrecoverable error. The component connects to the configured ZeroMQ endpoint
and sends a JSON message containing the module name and any serialisable state.
RAZAR takes ownership of the recovery process:

1. Save the provided state to disk.
2. Apply fixes (placeholder for custom logic).
3. Restart the affected module.
4. Restore the saved state after restart.

A confirmation response is sent back to the component once recovery completes.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import zmq
except Exception:  # pragma: no cover - optional dependency
    zmq = None  # type: ignore


logger = logging.getLogger(__name__)


class RecoveryManager:
    """Coordinate recovery actions for failed modules."""

    def __init__(self, endpoint: str, *, state_dir: Path | None = None) -> None:
        if zmq is None:  # pragma: no cover - dependency check
            raise RuntimeError("pyzmq is required for RecoveryManager")
        self.endpoint = endpoint
        self.state_dir = state_dir or Path("recovery_state")
        self.state_dir.mkdir(parents=True, exist_ok=True)
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

        self.save_state(module, state)
        self.apply_fixes(module)
        self.restart_module(module)
        self.restore_state(module, state)

    # ------------------------------------------------------------------
    def save_state(self, module: str, state: Dict[str, Any]) -> None:
        """Persist the provided ``state`` for ``module``."""

        path = self.state_dir / f"{module}.json"
        path.write_text(json.dumps(state), encoding="utf-8")
        logger.info("State for %s saved to %s", module, path)

    # ------------------------------------------------------------------
    def apply_fixes(self, module: str) -> None:  # pragma: no cover - placeholder
        """Apply corrective actions for ``module``.

        Subclasses or callers should override this to implement domain-specific
        fixes such as patching configuration files or restoring packages.
        """

        logger.info("Applying fixes for %s", module)

    # ------------------------------------------------------------------
    def restart_module(self, module: str) -> None:  # pragma: no cover - placeholder
        """Restart the failed ``module``."""

        logger.info("Restarting module %s", module)

    # ------------------------------------------------------------------
    def restore_state(self, module: str, state: Dict[str, Any]) -> None:  # pragma: no cover - placeholder
        """Restore ``state`` to ``module`` after restart."""

        logger.info("Restoring state for %s", module)

    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close ZeroMQ resources."""

        self.socket.close(0)
        self.context.term()
