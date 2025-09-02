"""Tests for the preflight module."""

import json


from tools import preflight


def test_check_optional_packages(monkeypatch):
    """Missing packages are reported and helper is invoked."""

    called = []

    def mock_check_optional(packages):
        called.append(packages)

    monkeypatch.setattr(preflight, "check_optional_packages", mock_check_optional)
    missing = preflight._check_optional_packages(["json", "fake_pkg"])

    assert missing == ["fake_pkg"]
    assert called == [["json", "fake_pkg"]]


def test_main_success(monkeypatch, capsys):
    """When all checks pass, a success message is shown."""

    monkeypatch.setattr(preflight, "check_required", lambda vars: None)
    monkeypatch.setattr(preflight, "_check_optional_packages", lambda pkgs: [])
    monkeypatch.setattr(preflight, "check_required_binaries", lambda bins: None)
    monkeypatch.setenv("HF_TOKEN", "x")
    monkeypatch.setenv("GLM_API_URL", "x")
    monkeypatch.setattr(preflight.sys, "argv", ["preflight"])

    assert preflight.main() == 0
    out = capsys.readouterr().out
    assert "All preflight checks passed." in out


def test_main_reports_issues(monkeypatch, capsys):
    """``--report`` emits structured JSON for problems."""

    def fail_env(vars):
        raise SystemExit("Missing required environment variable: TEST")

    def fail_bins(bins):
        raise SystemExit("Missing required binaries: FOO")

    monkeypatch.setattr(preflight, "check_required", fail_env)
    monkeypatch.setattr(preflight, "_check_optional_packages", lambda pkgs: ["pkg"])
    monkeypatch.setattr(preflight, "check_required_binaries", fail_bins)
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("GLM_API_URL", "")
    monkeypatch.setattr(preflight.sys, "argv", ["preflight", "--report"])

    assert preflight.main() == 1
    data = json.loads(capsys.readouterr().out)
    assert data["env"]
    assert data["packages"]
    assert data["binaries"]
