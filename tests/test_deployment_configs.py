"""Tests for deployment configs."""

import json
from pathlib import Path

import yaml


def test_kubernetes_manifest():
    data = yaml.safe_load(Path("deployment/kubernetes/deployment.yaml").read_text())
    assert data["kind"] == "Deployment"
    containers = data["spec"]["template"]["spec"]["containers"]
    assert containers and "image" in containers[0]


def test_serverless_manifest():
    data = json.loads(Path("deployment/serverless/function.json").read_text())
    assert data["runtime"].startswith("python")
    assert data["events"]


def test_docker_compose_production():
    data = yaml.safe_load(Path("docker-compose.production.yml").read_text())
    assert "services" in data
    image = data["services"]["app"]["image"]
    assert "${APP_VERSION}" in image
