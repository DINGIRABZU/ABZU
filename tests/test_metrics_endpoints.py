from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_fastapi_instrumentator import Instrumentator


def _collect_metrics(app: FastAPI) -> str:
    Instrumentator().instrument(app).expose(app)
    with TestClient(app) as client:
        resp = client.get("/metrics")
    return resp.text


def test_crown_metrics_endpoint_exposes_boot_gauge() -> None:
    import crown_router  # noqa: F401  # ensure gauge is registered

    app = FastAPI()
    metrics = _collect_metrics(app)
    assert 'service_boot_duration_seconds{service="crown"}' in metrics


def test_bana_metrics_endpoint_exposes_boot_gauge() -> None:
    from bana import narrative_api

    app = FastAPI()
    app.include_router(narrative_api.router)
    metrics = _collect_metrics(app)
    assert 'service_boot_duration_seconds{service="bana"}' in metrics


def test_memory_metrics_endpoint_exposes_boot_gauge() -> None:
    from memory import narrative_engine  # noqa: F401  # ensure gauge is registered

    app = FastAPI()
    metrics = _collect_metrics(app)
    assert 'service_boot_duration_seconds{service="memory"}' in metrics
