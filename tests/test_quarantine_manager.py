"""Tests for quarantine manager."""

from __future__ import annotations

import sys
from pathlib import Path
import json
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import razar.quarantine_manager as qm


def test_quarantine_records_diagnostics(tmp_path, monkeypatch):
    quarantine_dir = tmp_path / "quarantine"
    log_file = tmp_path / "log.md"
    monkeypatch.setattr(qm, "QUARANTINE_DIR", quarantine_dir)
    monkeypatch.setattr(qm, "LOG_FILE", log_file)

    component = {"name": "alpha"}
    diagnostics = {"error": "stack"}
    qm.quarantine_component(component, "boom", diagnostics=diagnostics)

    assert (quarantine_dir / "alpha.json").exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "quarantined" in log_text
    assert json.dumps(diagnostics, sort_keys=True) in log_text


def test_reactivate_requires_verification(tmp_path, monkeypatch):
    quarantine_dir = tmp_path / "quarantine"
    log_file = tmp_path / "log.md"
    monkeypatch.setattr(qm, "QUARANTINE_DIR", quarantine_dir)
    monkeypatch.setattr(qm, "LOG_FILE", log_file)

    component = {"name": "beta"}
    qm.quarantine_component(component, "fail")

    with pytest.raises(ValueError):
        qm.reactivate_component("beta", verified=False)

    qm.reactivate_component("beta", verified=True, automated=True, note="patched")
    assert not (quarantine_dir / "beta.json").exists()
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert any("reactivated" in line and "auto" in line for line in lines)
