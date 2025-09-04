"""API for chakra metrics and advice logging."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import requests  # type: ignore[import]
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

PROM_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
ADVICE_PATH = Path("data") / "chakra_advice.jsonl"


class Advice(BaseModel):
    """Request body for logging chakra advice."""

    advice: str


def _query_prometheus(expr: str) -> list[dict[str, Any]]:
    """Run a Prometheus query ``expr`` and return the result list."""

    resp = requests.get(f"{PROM_URL}/api/v1/query", params={"query": expr}, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", {}).get("result", [])


@router.get("/metrics/{chakra}")
def chakra_metrics(chakra: str) -> dict[str, float | str]:
    """Return Prometheus metric value for ``chakra``."""

    expr = f'chakra_energy{{chakra="{chakra}"}}'
    result = _query_prometheus(expr)
    if not result:
        raise HTTPException(status_code=404, detail="Metric not found")
    try:
        value = float(result[0]["value"][1])
    except (KeyError, IndexError, ValueError) as exc:  # pragma: no cover - sanity
        raise HTTPException(
            status_code=500, detail="Malformed Prometheus response"
        ) from exc
    return {"chakra": chakra, "value": value}


@router.post("/advice/{chakra}")
def chakra_advice(chakra: str, advice: Advice) -> dict[str, str]:
    """Log a piece of advice for ``chakra``."""

    ADVICE_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "chakra": chakra,
        "advice": advice.advice,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    with ADVICE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return {"status": "ok"}


__all__ = ["router"]
