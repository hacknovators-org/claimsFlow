import streamlit as st
import asyncio
import json
import time
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.components.header import render_header
from ui.components.status_display import render_status_display
from ui.components.progress_tracker import render_progress_tracker
from ui.components.report_viewer import render_report_viewer
from ui.services.websocket_client import WebSocketClient
from ui.utils.session_state import initialize_session_state

st.set_page_config(
    page_title="Claims Processing Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    initialize_session_state()
    
    render_header()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Agent Control")
        
        if not st.session_state.processing:
            if st.button("🚀 Start Claims Processing", type="primary", use_container_width=True):
                start_processing()
        else:
            st.button("⏸️ Processing...", disabled=True, use_container_width=True)
            
            if st.button("🛑 Stop Processing", type="secondary", use_container_width=True):
                stop_processing()
        
        st.markdown("---")
        render_status_display()
    
    with col2:
        if st.session_state.processing or st.session_state.completed:
            render_progress_tracker()
    
    if st.session_state.completed and st.session_state.report_data:
        st.markdown("---")
        render_report_viewer()

def start_processing():
    st.session_state.processing = True
    st.session_state.completed = False
    st.session_state.start_time = datetime.now()
    st.session_state.progress_data = []
    st.session_state.current_stage = "Initializing..."
    st.session_state.progress = 0.0
    
    with st.spinner("Starting claims processing..."):
        try:
            client = WebSocketClient()
            result = asyncio.run(client.start_processing_sync())
            
            if result.get("success"):
                st.session_state.processing = False
                st.session_state.completed = True
                st.session_state.report_data = result.get("results", {})
                st.session_state.processing_result = result
                st.success("✅ Claims processing completed successfully!")
                st.rerun()
            else:
                st.session_state.processing = False
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.session_state.processing = False
            st.error(f"❌ Error starting processing: {str(e)}")

def stop_processing():
    st.session_state.processing = False
    st.session_state.current_stage = "Stopped"
    st.warning("⏸️ Processing stopped by user")

if __name__ == "__main__":
    main()