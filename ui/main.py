import sys
import os

# Add the root directory to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import streamlit as st

from ui.theme import inject_css, tone_key_for_recommendation
from ui.components.header import render_header
from ui.components.status_display import render_status_display
from ui.components.progress_tracker import render_progress_tracker
from ui.components.report_viewer import render_report_viewer
from ui.components.history_view import render_history_view
from ui.components.ui import empty_state, stat_row
from ui.servicesui import processing_client
from ui.servicesui.ws_subscriber import get_or_create_subscriber
from ui.utils.session_state import initialize_session_state, start_new_run

st.set_page_config(
    page_title="Claims Processing Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    initialize_session_state()
    inject_css()

    subscriber = get_or_create_subscriber(st.session_state, processing_client.ws_url())

    render_header()
    render_sidebar_controls()

    nav = st.sidebar.radio("View", ["Processing", "History"])
    if nav == "History":
        render_history_view()
        return

    view = st.session_state.run.view

    if view == "idle":
        render_idle_view()
    elif view == "running":
        render_running_view(subscriber)
    elif view == "completed":
        _ensure_result_fetched()
        render_status_display()
        st.markdown("---")
        render_report_viewer()
    elif view == "failed":
        render_status_display()


def render_sidebar_controls():
    run = st.session_state.run
    st.sidebar.markdown("### Agent Control")

    if run.view in ("idle", "completed", "failed"):
        if st.sidebar.button("Start Claims Processing", type="primary", use_container_width=True):
            start_processing()
    else:
        st.sidebar.button("Processing...", disabled=True, use_container_width=True)
        if run.root_agent_id and st.sidebar.button("Stop Processing", type="secondary", use_container_width=True):
            stop_processing(run.root_agent_id)


def start_processing():
    try:
        result = processing_client.start_processing()
    except Exception as e:
        st.sidebar.error(f"Could not reach the processing API: {e}")
        return

    if not result.get("started"):
        st.sidebar.warning(result.get("reason", "Could not start processing"))
        return

    start_new_run(result.get("sender_email"))
    st.rerun()


def stop_processing(agent_id: str):
    try:
        processing_client.stop_agent(agent_id)
    except Exception as e:
        st.sidebar.error(f"Failed to stop processing: {e}")


def render_idle_view():
    try:
        stats = processing_client.get_status()
    except Exception as e:
        st.error(f"Could not reach the processing API: {e}")
        return

    if not stats.get("total_processed"):
        empty_state("No processing runs yet. Start one from the sidebar to see live progress here.", icon="🚀")
        return

    last = stats.get("last_processing") or {}
    stat_row([
        ("Total Runs", str(stats.get("total_processed", 0)), "neutral"),
        ("Success Rate", f"{stats.get('success_rate', 0):.0f}%", "success"),
        ("Last Recommendation", last.get("recommendation", "—"),
         tone_key_for_recommendation(last.get("recommendation", ""))),
    ])
    st.caption("Start a new run from the sidebar, or switch to History for the full run log.")


def render_running_view(subscriber):
    _live_fragment(subscriber)


@st.fragment(run_every=1.0)
def _live_fragment(subscriber):
    for message in subscriber.drain():
        st.session_state.run.apply_update(message)

    if st.session_state.run.view != "running":
        # Run reached a terminal state - break out of the fragment-scoped
        # rerun and let the next full script run switch to Completed/Failed.
        st.rerun()
        return

    render_status_display()
    st.markdown("---")
    render_progress_tracker()


def _ensure_result_fetched():
    run = st.session_state.run
    if run.result_fetched or not run.root_agent_id:
        return
    try:
        run.final_result = processing_client.get_result(run.root_agent_id)
    except Exception:
        run.final_result = None
    run.result_fetched = True


if __name__ == "__main__":
    main()
