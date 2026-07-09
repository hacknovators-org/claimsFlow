import pandas as pd
import streamlit as st

from ui.components.ui import empty_state, stat_row
from ui.servicesui import processing_client


def render_history_view():
    """Run-log table backed by pipeline.get_processing_history() - the same
    history whether a run was triggered from this UI or from SMS
    (routes/sms.py), since both go through pipeline_singleton (WORKFLOW.md
    §2.2/§5.5)."""
    st.subheader("Processing History")

    try:
        stats = processing_client.get_status()
        history = processing_client.get_history()
    except Exception as e:
        st.error(f"Could not reach the processing API: {e}")
        return

    if not history:
        empty_state("No processing runs yet. Runs triggered from the UI or via SMS will show up here.", icon="🗂️")
        return

    stat_row([
        ("Total Runs", str(stats.get("total_processed", 0)), "neutral"),
        ("Success Rate", f"{stats.get('success_rate', 0):.0f}%", "success"),
        ("Active Agents", str(stats.get("active_agents", 0)), "info" if stats.get("active_agents") else "neutral"),
    ])

    st.markdown("---")

    rows = [
        {
            "Agent ID": record.get("agent_id"),
            "Sender": record.get("sender_email"),
            "Status": record.get("status"),
            "Recommendation": record.get("recommendation", "—"),
            "Critical Issues": record.get("critical_issues_count", "—"),
            "Duration (s)": round(record.get("duration_seconds", 0), 1) if record.get("duration_seconds") else "—",
            "Ended": record.get("end_time"),
        }
        for record in reversed(history)
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
