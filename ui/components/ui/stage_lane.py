import streamlit as st

from ui.theme import tone_key_for_agent_status, TONES
from ui.utils.stage_taxonomy import LANES
from .status_pill import status_pill


def stage_lane(lane_key: str, latest_update: dict | None):
    """Render one sub-agent's live stage list + progress.

    `latest_update` is the most recent AgentUpdate dict broadcast for this
    lane (or None if the lane hasn't emitted anything yet this run).
    """
    display_name, stages = LANES[lane_key]

    status = (latest_update or {}).get("status", "initialized")
    progress = (latest_update or {}).get("progress", 0.0)
    message = (latest_update or {}).get("message", "Waiting to start...")
    error = (latest_update or {}).get("error")

    with st.container(border=True):
        header_col, pill_col = st.columns([3, 2])
        with header_col:
            st.markdown(f"**{display_name}**")
        with pill_col:
            status_pill(status.capitalize(), tone=tone_key_for_agent_status(status))

        st.progress(min(max(progress / 100.0, 0.0), 1.0))

        if error:
            st.markdown(
                f'<span style="color:{TONES["danger"].fg};">{TONES["danger"].icon} {error}</span>',
                unsafe_allow_html=True,
            )
        else:
            st.caption(message)

        with st.expander("Stages", expanded=(status == "processing")):
            current_stage = (latest_update or {}).get("stage")
            for stage_key, stage_label, threshold in stages:
                if status == "failed" and stage_key == current_stage:
                    marker, color = "✕", TONES["danger"].fg
                elif progress >= threshold:
                    marker, color = "✓", TONES["success"].fg
                elif stage_key == current_stage:
                    marker, color = "●", TONES["info"].fg
                else:
                    marker, color = "○", TONES["neutral"].fg
                st.markdown(
                    f'<span style="color:{color};">{marker}</span> {stage_label}',
                    unsafe_allow_html=True,
                )
