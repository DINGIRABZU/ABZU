from pathlib import Path

from agents.razar.ignition_builder import build_ignition


def test_build_ignition(tmp_path: Path) -> None:
    blueprint = tmp_path / "system_blueprint.md"
    blueprint.write_text(
        """
### Alpha
- **Priority:** 1
- **Health Check:** check alpha

### Beta
- **Priority:** 2
- **Health Check:** check beta

## Staged Startup Order
0. Alpha (priority 1)
1. Beta (priority 2)
        """,
        encoding="utf-8",
    )

    output = tmp_path / "Ignition.md"
    build_ignition(blueprint, output)

    content = output.read_text(encoding="utf-8")
    assert "## Priority 1" in content
    assert "## Priority 2" in content
    assert "| 0 | Alpha | check alpha | ⚠️ |" in content
    assert "| 1 | Beta | check beta | ⚠️ |" in content
