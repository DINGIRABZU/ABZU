import streamlit as st
import pandas as pd
from INANNA_AI import db_storage, gate_orchestrator

st.set_page_config(page_title="LLM Metrics Dashboard")

st.title("LLM Performance Metrics")

metrics = db_storage.fetch_benchmarks()
if metrics:
    df = pd.DataFrame(metrics)
    st.line_chart(df.set_index("timestamp")[["response_time", "coherence", "relevance"]])
else:
    st.write("No benchmark data available.")

predictor = gate_orchestrator.GateOrchestrator()
pred = predictor.predict_best_llm()

st.markdown(f"**Predicted best model:** `{pred}`")

