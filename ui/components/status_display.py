from datetime import datetime

import streamlit as st

from ui.components.ui import stat_row
from ui.theme import tone_key_for_recommendation, tone_key_for_risk


def render_status_display():
    """Run summary strip. Composes the same tone system used everywhere else
    (ui.theme) so a recommendation of APPROVE and a risk level of LOW read as
    the same "good" green - they no longer take different code paths with
    different semantics (WORKFLOW.md §2.3)."""
    st.subheader("Processing Status")
    run = st.session_state.run

    if run.view == "failed":
        _render_progress_row(run)
        if run.error:
            st.error(f"Processing failed: {run.error}")
        else:
            st.warning(f"Processing stopped: {run.message or 'Stopped by user'}")
        return

    if run.view == "completed" and run.final_result:
        _render_outcome_row(run.final_result)
        return

    if run.view == "running":
        _render_progress_row(run)
        return

    st.info("Ready to start processing")


def _render_progress_row(run):
    items = []
    if run.started_at:
        elapsed = int((datetime.now() - run.started_at).total_seconds())
        items.append(("Processing Time", f"{elapsed}s", "neutral"))

    master = run.lane_updates.get("master")
    if master:
        items.append(("Current Stage", master.get("stage", "—").replace("_", " ").title(), "neutral"))
        items.append(("Progress", f"{master.get('progress', 0):.0f}%", "neutral"))

    if items:
        stat_row(items)


def _render_outcome_row(final_result: dict):
    recommendation = final_result.get("overall_recommendation", "UNKNOWN")
    fraud_risk = final_result.get("fraud_risk_level", "UNKNOWN")
    critical_issues = final_result.get("critical_issues", [])

    stat_row([
        ("Recommendation", recommendation, tone_key_for_recommendation(recommendation)),
        ("Fraud Risk", fraud_risk, tone_key_for_risk(fraud_risk)),
        ("Critical Issues", str(len(critical_issues)), "danger" if critical_issues else "success"),
    ])
