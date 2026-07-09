import streamlit as st

from ui.theme import TONES


def metric_card(label: str, value: str, tone: str = "neutral"):
    """A single metric tile with card chrome (replaces bare st.metric)."""
    t = TONES.get(tone, TONES["neutral"])
    st.markdown(
        f'''<div class="cf-metric-card" style="border-color:{t.border};">
            <div class="cf-metric-label">{label}</div>
            <div class="cf-metric-value" style="color:{t.fg};">{value}</div>
        </div>''',
        unsafe_allow_html=True,
    )


def stat_row(items: list[tuple[str, str, str]]):
    """Render a row of metric_card tiles. items: list of (label, value, tone)."""
    cols = st.columns(len(items))
    for col, (label, value, tone) in zip(cols, items):
        with col:
            metric_card(label, value, tone)
