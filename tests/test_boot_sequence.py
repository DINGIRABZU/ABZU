import json

import pytest

from tests.helpers.boot_sequence import boot_sequence
from razar import boot_orchestrator
from razar.bootstrap_utils import STATE_FILE


def _clear_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def test_boot_sequence_success(boot_config_path):
    _clear_state()
    boot_sequence(boot_config_path)
    data = json.loads(STATE_FILE.read_text())
    assert data["probes"]["basic_service"]["status"] == "ok"
    assert data["probes"]["complex_service"]["status"] == "ok"


def test_boot_sequence_failure():
    _clear_state()
    bad = {
        "name": "bad_service",
        "command": ["python", "-c", "print('bad service')"],
        "health_check": ["python", "-c", "import sys; sys.exit(1)"],
    }
    with pytest.raises(RuntimeError):
        boot_orchestrator.launch_component(bad)
    data = json.loads(STATE_FILE.read_text())
    assert data["probes"]["bad_service"]["status"] == "fail"
