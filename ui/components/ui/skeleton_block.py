import streamlit as st


def skeleton_block(lines: int = 3):
    """Shown while waiting for the first WS message after a run starts,
    instead of a jump-cut from idle straight to live data."""
    widths = ["100%", "85%", "60%"]
    for i in range(lines):
        width = widths[i % len(widths)]
        st.markdown(
            f'<div class="cf-skeleton" style="width:{width};"></div>',
            unsafe_allow_html=True,
        )
