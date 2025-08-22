from __future__ import annotations

"""Streamlit app displaying LLM performance metrics."""

import logging

import pandas as pd
import streamlit as st

from INANNA_AI import db_storage, gate_orchestrator


LOGGER = logging.getLogger(__name__)

st.set_page_config(page_title="LLM Metrics Dashboard")

st.title("LLM Performance Metrics")

try:
    metrics = db_storage.fetch_benchmarks()
except Exception as exc:  # pragma: no cover - external service failure
    LOGGER.exception("Failed to fetch benchmarks: %s", exc)
    metrics = []

if metrics:
    df = pd.DataFrame(metrics)
    st.line_chart(
        df.set_index("timestamp")[["response_time", "coherence", "relevance"]]
    )
else:
    st.write("No benchmark data available.")

try:
    predictor = gate_orchestrator.GateOrchestrator()
    pred = predictor.predict_best_llm()
except Exception as exc:  # pragma: no cover - external service failure
    LOGGER.exception("Failed to predict best model: %s", exc)
    pred = "unknown"

st.markdown(f"**Predicted best model:** `{pred}`")
