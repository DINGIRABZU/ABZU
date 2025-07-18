import streamlit as st
import pandas as pd
from INANNA_AI import db_storage, adaptive_learning

st.set_page_config(page_title="RL Metrics Dashboard")

st.title("Reinforcement Learning Metrics")

feedback = db_storage.fetch_feedback(limit=100)
if feedback:
    df = pd.DataFrame(feedback)
    st.line_chart(
        df.set_index("timestamp")[[
            "satisfaction",
            "ethical_alignment",
            "existential_clarity",
        ]]
    )
else:
    st.write("No feedback data available.")

st.subheader("Validator Threshold")
st.markdown(
    f"**Current threshold:** {adaptive_learning.THRESHOLD_AGENT.threshold:.2f}"
)

