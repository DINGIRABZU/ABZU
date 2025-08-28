from __future__ import annotations

"""Operator command dispatcher with access controls and log mirroring."""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable


class OperatorDispatcher:
    """Dispatch commands from operators to agents with audit logging.

    Parameters
    ----------
    access_map:
        Mapping of operator identifiers to the set of agents they may invoke.
    log_dir:
        Directory where per-operator private channels are stored.
    worm_dir:
        Directory for append-only mirrors of Cocytus/Victim logs.
    """

    def __init__(
        self,
        access_map: Dict[str, Iterable[str]],
        *,
        log_dir: Path | str = Path("logs/operators"),
        worm_dir: Path | str = Path("audit_logs"),
    ) -> None:
        self.access_map = {k: set(v) for k, v in access_map.items()}
        self.log_dir = Path(log_dir)
        self.worm_dir = Path(worm_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.worm_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def dispatch(
        self,
        operator: str,
        agent: str,
        command: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Execute ``command`` on behalf of ``operator`` for ``agent``.

        Raises ``PermissionError`` if the operator lacks access to the agent.
        All invocations are recorded to per-operator logs. Commands targeting
        ``cocytus`` or ``victim`` are mirrored to append-only audit logs.
        """

        if agent not in self.access_map.get(operator, set()):
            raise PermissionError(f"{operator} cannot access {agent}")

        result = command(*args, **kwargs)
        record = {
            "operator": operator,
            "agent": agent,
            "command": getattr(command, "__name__", "<callable>"),
            "args": args,
            "kwargs": kwargs,
        }
        self._record_private(operator, record)
        if agent.lower() in {"cocytus", "victim"}:
            self._worm_mirror(agent.lower(), record)
        return result

    # ------------------------------------------------------------------
    def _record_private(self, operator: str, record: Dict[str, Any]) -> None:
        path = self.log_dir / f"{operator}.log"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    # ------------------------------------------------------------------
    def _worm_mirror(self, agent: str, record: Dict[str, Any]) -> None:
        path = self.worm_dir / f"{agent}.log"
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
        with os.fdopen(fd, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")


__all__ = ["OperatorDispatcher"]
