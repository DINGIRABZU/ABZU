"""Tests for mission brief rotation."""

from pathlib import Path
import os

from razar import boot_orchestrator as bo

__version__ = "0.1.0"


def test_mission_brief_rotation(tmp_path: Path) -> None:
    archive_dir = tmp_path / "mission_briefs"
    archive_dir.mkdir(parents=True)
    for i in range(5):
        brief = archive_dir / f"{i}.json"
        response = archive_dir / f"{i}_response.json"
        brief.write_text("{}")
        response.write_text("{}")
        os.utime(brief, (i, i))
        os.utime(response, (i, i))

    bo._rotate_mission_briefs(archive_dir, limit=3)
    briefs = [p for p in archive_dir.glob("*.json") if "_response" not in p.name]
    assert len(briefs) == 3
    assert not (archive_dir / "0.json").exists()
