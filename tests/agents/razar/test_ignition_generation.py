from pathlib import Path

from agents.razar.ignition_builder import build_ignition


def test_build_ignition_from_repo_blueprint(tmp_path: Path) -> None:
    """Ensure the builder creates an ignition file from the repo blueprint."""
    root = Path(__file__).resolve().parents[3]
    blueprint = root / "docs" / "system_blueprint.md"
    output = tmp_path / "Ignition.md"

    build_ignition(blueprint, output)
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert "| 0 | RAZAR Startup Orchestrator" in content
    assert "| 7 | Video" in content
    assert "⚠️" in content
