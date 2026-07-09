"""One typed state object for the whole app (WORKFLOW.md §2.4) instead of
nine independent st.session_state keys with no shared shape.

Streamlit reruns the whole script on every interaction; RunState.view is a
computed property (never a separately-tracked flag that can drift out of
sync with the updates that actually arrived) so "what screen are we on" is
always derived fresh from the latest AgentUpdate stream.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import streamlit as st

from ui.utils.stage_taxonomy import lane_for_agent_id, root_agent_id as extract_root_id


@dataclass
class RunState:
    started: bool = False
    started_at: Optional[datetime] = None
    root_agent_id: Optional[str] = None
    sender_email: Optional[str] = None
    lane_updates: dict = field(default_factory=dict)  # lane_key -> latest AgentUpdate dict
    final_result: Optional[dict] = None
    result_fetched: bool = False
    error: Optional[str] = None
    message: Optional[str] = None

    @property
    def view(self) -> str:
        master = self.lane_updates.get("master")
        if master is None:
            # started-but-no-update-yet still reads as "running" (with a
            # skeleton in place of live data) rather than jump-cutting
            # straight from idle to a populated tracker (WORKFLOW.md §5.4).
            return "running" if self.started else "idle"
        status = master.get("status")
        if status in ("failed", "paused"):
            # "paused" only happens via a user-initiated stop
            # (agents/master_agent.py stop_processing) - it's a distinct
            # terminal state from "failed" but reuses the same view bucket;
            # render_status_display tells them apart via `error`.
            return "failed"
        if status == "completed":
            return "completed"
        return "running"

    def apply_update(self, update: dict):
        lane = lane_for_agent_id(update["agent_id"])
        incoming_root = extract_root_id(update["agent_id"])

        is_new_run_start = (
            lane == "master"
            and incoming_root != self.root_agent_id
            and update.get("status") not in ("completed", "failed")
        )
        if is_new_run_start:
            # Only one agent can be active pipeline-wide (routes/processing.py
            # rejects /start while one is running), so a new master run
            # showing up always means the previously tracked run is over -
            # start this run's view from a clean slate.
            self.root_agent_id = incoming_root
            self.lane_updates = {}
            self.final_result = None
            self.result_fetched = False
            self.error = None

        if self.root_agent_id is not None and incoming_root != self.root_agent_id:
            return  # stale broadcast from a run this session isn't tracking

        self.lane_updates[lane] = update
        if lane == "master":
            self.message = update.get("message")
            if update.get("status") == "failed":
                self.error = update.get("error")


def initialize_session_state():
    if "run" not in st.session_state:
        st.session_state.run = RunState()


def start_new_run(sender_email: str):
    st.session_state.run = RunState(sender_email=sender_email, started=True, started_at=datetime.now())
