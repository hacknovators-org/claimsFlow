import streamlit as st

from ui.theme import TONES


def status_pill(label: str, tone: str = "neutral", *, show_icon: bool = True):
    """A single semantic status badge. `tone` is one of ui.theme.TONES keys
    ("success", "danger", "warning", "info", "neutral") - resolve business
    values (recommendation, risk level, agent status) to a tone via
    ui.theme.tone_for_* before calling this."""
    t = TONES.get(tone, TONES["neutral"])
    icon = f"{t.icon} " if show_icon else ""
    st.markdown(
        f'<span class="cf-pill" style="color:{t.fg}; background:{t.bg}; '
        f'border:1px solid {t.border};">{icon}{label}</span>',
        unsafe_allow_html=True,
    )
