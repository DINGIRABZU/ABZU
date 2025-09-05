from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.verify_self_healing as vsh


def _setup_env(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "self_healing_manifesto.md").write_text("manifesto")
    (docs / "INDEX.md").write_text("self_healing_manifesto.md")
    logs = tmp_path / "logs"
    logs.mkdir()
    ts = datetime.now(timezone.utc).isoformat()
    (logs / "self_heal.jsonl").write_text(
        json.dumps({"timestamp": ts, "status": "success"}) + "\n"
    )
    (tmp_path / "quarantine").mkdir()


def test_verify_self_healing_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_env(tmp_path)
    monkeypatch.setattr(vsh, "DOCS_INDEX", tmp_path / "docs" / "INDEX.md")
    monkeypatch.setattr(vsh, "MANIFEST", tmp_path / "docs" / "self_healing_manifesto.md")
    monkeypatch.setattr(vsh, "SELF_HEAL_LOG", tmp_path / "logs" / "self_heal.jsonl")
    monkeypatch.setattr(vsh, "QUARANTINE_DIR", tmp_path / "quarantine")
    assert vsh.verify_self_healing() == 0


def test_missing_manifest_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_env(tmp_path)
    (tmp_path / "docs" / "INDEX.md").write_text("other.md")
    monkeypatch.setattr(vsh, "DOCS_INDEX", tmp_path / "docs" / "INDEX.md")
    monkeypatch.setattr(vsh, "MANIFEST", tmp_path / "docs" / "self_healing_manifesto.md")
    monkeypatch.setattr(vsh, "SELF_HEAL_LOG", tmp_path / "logs" / "self_heal.jsonl")
    monkeypatch.setattr(vsh, "QUARANTINE_DIR", tmp_path / "quarantine")
    assert vsh.verify_self_healing() == 1


def test_stale_quarantine_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_env(tmp_path)
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    data = {"quarantined_at": old.isoformat()}
    qfile = tmp_path / "quarantine" / "comp.json"
    qfile.write_text(json.dumps(data))
    monkeypatch.setattr(vsh, "DOCS_INDEX", tmp_path / "docs" / "INDEX.md")
    monkeypatch.setattr(vsh, "MANIFEST", tmp_path / "docs" / "self_healing_manifesto.md")
    monkeypatch.setattr(vsh, "SELF_HEAL_LOG", tmp_path / "logs" / "self_heal.jsonl")
    monkeypatch.setattr(vsh, "QUARANTINE_DIR", tmp_path / "quarantine")
    assert vsh.verify_self_healing(max_quarantine_hours=24) == 1


def test_missing_recent_cycle_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _setup_env(tmp_path)
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    (tmp_path / "logs" / "self_heal.jsonl").write_text(
        json.dumps({"timestamp": old.isoformat(), "status": "success"}) + "\n"
    )
    monkeypatch.setattr(vsh, "DOCS_INDEX", tmp_path / "docs" / "INDEX.md")
    monkeypatch.setattr(vsh, "MANIFEST", tmp_path / "docs" / "self_healing_manifesto.md")
    monkeypatch.setattr(vsh, "SELF_HEAL_LOG", tmp_path / "logs" / "self_heal.jsonl")
    monkeypatch.setattr(vsh, "QUARANTINE_DIR", tmp_path / "quarantine")
    assert vsh.verify_self_healing(max_cycle_hours=24) == 1
