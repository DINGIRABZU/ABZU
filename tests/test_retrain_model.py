"""Tests for retrain model."""

from __future__ import annotations

import sys
import types

import auto_retrain


def test_retrain_model_logs(monkeypatch):
    logged = {}

    class DummyRun:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def start_run(run_name=None):
        logged["run_name"] = run_name
        return DummyRun()

    def log_param(name, value):
        logged[name] = value

    dummy_mlflow = types.SimpleNamespace(start_run=start_run, log_param=log_param)
    sys.modules["mlflow"] = dummy_mlflow

    monkeypatch.setattr(
        auto_retrain, "trigger_finetune", lambda d: logged.setdefault("trigger", len(d))
    )
    auto_retrain.retrain_model([{"prompt": "p", "completion": "c"}])
    assert logged["run_name"] == "auto_retrain"
    assert logged["examples"] == 1
    assert logged["trigger"] == 1
