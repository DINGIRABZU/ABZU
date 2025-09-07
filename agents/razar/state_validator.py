"""State file validation utilities for RAZAR."""

from __future__ import annotations

__version__ = "0.2.2"
__all__ = ["validate_state", "DEFAULT_STATE"]

import json
from pathlib import Path

try:  # pragma: no cover - dependency is handled in tests
    import jsonschema
except Exception as exc:  # pragma: no cover
    raise RuntimeError("jsonschema is required for state validation") from exc

DEFAULT_STATE = {
    "last_component": "",
    "capabilities": [],
    "downtime": {},
    "launched_models": [],
    "handshake": {
        "acknowledgement": "",
        "capabilities": [],
        "downtime": {},
    },
    "glm4v_present": False,
    "events": [],
}


def validate_state(path: Path | str) -> None:
    """Validate the state file at ``path`` against the schema.

    If the file is missing or fails validation, a backup is created and a
    fresh state file based on ``DEFAULT_STATE`` is written.
    """

    state_path = Path(path)
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "docs" / "schemas" / "razar_state.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    valid = False
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding="utf-8"))
            jsonschema.validate(data, schema)
            valid = True
        except (json.JSONDecodeError, jsonschema.ValidationError):
            backup_path = state_path.with_suffix(state_path.suffix + ".bak")
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.replace(backup_path)

    if not valid:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(DEFAULT_STATE), encoding="utf-8")
