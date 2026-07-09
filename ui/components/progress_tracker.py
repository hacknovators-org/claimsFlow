import streamlit as st

from ui.components.ui import stage_lane, skeleton_block
from ui.utils.stage_taxonomy import LANE_ORDER


def render_progress_tracker():
    """4-lane live view (master + 3 sub-agents), driven entirely by the real
    AgentUpdate stream demuxed by agent_id - no fabricated stage list, no
    client-side progress simulation."""
    st.subheader("Agent Processing Stages")

    run = st.session_state.run

    if not run.lane_updates:
        skeleton_block(lines=4)
        return

    cols = st.columns(2)
    for i, lane_key in enumerate(LANE_ORDER):
        with cols[i % 2]:
            stage_lane(lane_key, run.lane_updates.get(lane_key))
