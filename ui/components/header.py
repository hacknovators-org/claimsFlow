import streamlit as st
from datetime import datetime

def render_header():
    st.title("🏢 Claims Processing Agent")
    st.markdown("**AI-Powered Reinsurance Claims Analysis & Processing**")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("📧 **Source Email:** wamitinewton@gmail.com")
    
    with col2:
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"🕐 **Time:** {current_time}")
    
    with col3:
        if st.session_state.get('processing', False):
            st.markdown("🔄 **Status:** Processing")
        elif st.session_state.get('completed', False):
            st.markdown("✅ **Status:** Complete")
        else:
            st.markdown("⭐ **Status:** Ready")
    
    st.markdown("---")