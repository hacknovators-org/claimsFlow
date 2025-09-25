import streamlit as st

def initialize_session_state():
    """Initialize all session state variables"""
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    
    if 'current_stage' not in st.session_state:
        st.session_state.current_stage = "Ready"
    
    if 'progress_data' not in st.session_state:
        st.session_state.progress_data = []
    
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None

def reset_session_state():
    """Reset session state for new processing"""
    st.session_state.processing = False
    st.session_state.completed = False
    st.session_state.start_time = None
    st.session_state.progress = 0.0
    st.session_state.current_stage = "Ready"
    st.session_state.progress_data = []
    st.session_state.report_data = None
    st.session_state.processing_result = None
    st.session_state.last_update = None