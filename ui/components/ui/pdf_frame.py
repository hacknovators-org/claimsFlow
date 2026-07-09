import base64

import streamlit as st


def pdf_frame(pdf_bytes: bytes, height: int = 800):
    """Embed a PDF inline.

    Streamlit has no native PDF viewer, so this is the one documented place
    in the codebase allowed to reach for a raw base64 <iframe> + unsafe_allow_html
    - every other component composes primitives instead of hand-rolling HTML
    (WORKFLOW.md §2.3/§5.4).
    """
    b64 = base64.b64encode(pdf_bytes).decode()
    st.markdown(
        f'''<iframe src="data:application/pdf;base64,{b64}"
                width="100%" height="{height}"
                style="border: 1px solid #D8DEE1; border-radius: 8px;">
        </iframe>''',
        unsafe_allow_html=True,
    )
