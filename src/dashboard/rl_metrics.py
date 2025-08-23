"""Streamlit dashboard for reinforcement learning metrics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from INANNA_AI import adaptive_learning, db_storage

st.set_page_config(page_title="RL Metrics Dashboard")

st.title("Reinforcement Learning Metrics")

feedback = db_storage.fetch_feedback(limit=100)
if feedback:
    df = pd.DataFrame(feedback)
    st.line_chart(
        df.set_index("timestamp")[
            [
                "satisfaction",
                "ethical_alignment",
                "existential_clarity",
            ]
        ]
    )
else:
    st.write("No feedback data available.")

st.subheader("Validator Threshold")
st.markdown(f"**Current threshold:** {adaptive_learning.THRESHOLD_AGENT.threshold:.2f}")
