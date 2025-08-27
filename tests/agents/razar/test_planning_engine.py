import json
from pathlib import Path

import yaml

from agents.razar import planning_engine as pe


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_plan_generation(tmp_path):
    knowledge = {
        "directed": True,
        "multigraph": False,
        "graph": {},
        "nodes": [{"id": "a"}, {"id": "b"}, {"id": "c"}],
        "links": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}],
    }
    kp = tmp_path / "razar_knowledge.json"
    _write_json(kp, knowledge)

    priorities = {
        "a": {"priority": "P3"},
        "b": {"priority": "P2"},
        "c": {"priority": "P1"},
    }
    pp = tmp_path / "component_priorities.yaml"
    pp.write_text(yaml.safe_dump(priorities), encoding="utf-8")

    log = tmp_path / "razar.log"
    log.write_text(
        "\n".join(
            [
                json.dumps({"component": "a", "status": "failure"}),
                json.dumps({"component": "b", "status": "success"}),
                json.dumps({"component": "b", "status": "failure"}),
                json.dumps({"component": "c", "status": "success"}),
            ]
        ),
        encoding="utf-8",
    )

    output = tmp_path / "plans.json"
    plans = pe.plan(
        knowledge_path=kp, output=output, log_path=log, priorities_path=pp
    )

    assert output.exists()
    assert plans["a"]["steps"] == ["c", "b", "a"]
    assert plans["b"]["criticality"] == 1
    assert plans["c"]["success_rate"] == 1.0
