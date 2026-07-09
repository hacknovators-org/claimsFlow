import streamlit as st


def empty_state(message: str, icon: str = "🗂️"):
    """Used anywhere a screen would otherwise render a dead gap: first load,
    no history yet, no report data, etc."""
    st.markdown(
        f'''<div class="cf-empty-state">
            <div class="cf-empty-icon">{icon}</div>
            <div>{message}</div>
        </div>''',
        unsafe_allow_html=True,
    )
