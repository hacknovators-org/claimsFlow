import streamlit as st
from datetime import datetime

from ui.components.ui import status_pill

_VIEW_LABEL = {
    "idle": ("Ready", "neutral"),
    "running": ("Processing", "info"),
    "completed": ("Complete", "success"),
    "failed": ("Failed", "danger"),
}


def render_header():
    st.title("Claims Processing Agent")
    st.caption("AI-Powered Reinsurance Claims Analysis & Processing")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        sender = st.session_state.run.sender_email or "—"
        st.markdown(f"**Source Email:** {sender}")

    with col2:
        st.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")

    with col3:
        label, tone = _VIEW_LABEL[st.session_state.run.view]
        status_pill(label, tone=tone)

    st.markdown("---")
