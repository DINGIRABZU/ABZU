import asyncio
import json
from pathlib import Path

__version__ = "0.1.0"


def test_validate_ignition_sequence(tmp_path: Path, monkeypatch) -> None:
    """Validate ignition flow produces readiness for each component."""

    from scripts import validate_ignition

    log_file = tmp_path / "ignition_validation.json"
    monkeypatch.setattr(validate_ignition, "LOG_FILE", log_file)

    exit_code = asyncio.run(validate_ignition.main())
    assert exit_code == 0

    data = json.loads(log_file.read_text())
    sequence = data["sequence"]
    names = [step["component"] for step in sequence]
    assert names == [
        "RAZAR",
        "Crown",
        "INANNA",
        "Albedo",
        "Nazarick",
        "Operator",
    ]
    assert all(step["ready"] for step in sequence)
