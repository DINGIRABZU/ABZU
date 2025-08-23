"""Streamlit dashboard for usage metrics."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import corpus_memory_logging
from core import feedback_logging

st.set_page_config(page_title="Usage Metrics")

st.title("Usage Metrics")

interactions = corpus_memory_logging.load_interactions()
feedback = feedback_logging.load_feedback()

st.metric("Total interactions", len(interactions))
st.metric("Feedback entries", len(feedback))

if interactions:
    st.subheader("Recent interactions")
    st.dataframe(pd.DataFrame(interactions).tail(20))

if feedback:
    st.subheader("Feedback")
    st.dataframe(pd.DataFrame(feedback))
