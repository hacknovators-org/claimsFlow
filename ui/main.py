import streamlit as st
import asyncio
import json
import time
from datetime import datetime
import sys
import os
import threading

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from ui.components.header import render_header
from ui.components.status_display import render_status_display
from ui.components.progress_tracker import render_progress_tracker, render_progress_timeline, render_stage_duration_chart
from ui.components.report_viewer import render_report_viewer
from ui.servicesui.websocket_client import WebSocketClient
from ui.utils.session_state import initialize_session_state, reset_session_state

st.set_page_config(
    page_title="Claims Processing Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    initialize_session_state()
    
    render_header()
    
    main_col, sidebar_col = st.columns([3, 1])
    
    with sidebar_col:
        render_control_panel()
        st.markdown("---")
        render_status_display()
        
        if st.session_state.get('processing') or st.session_state.get('completed'):
            render_quick_stats()
    
    with main_col:
        if st.session_state.get('processing') or st.session_state.get('completed'):
            tab1, tab2, tab3 = st.tabs(["🔄 Live Progress", "📈 Analytics", "📊 Results"])
            
            with tab1:
                render_progress_tracker()
            
            with tab2:
                render_analytics_tab()
            
            with tab3:
                if st.session_state.get('completed') and st.session_state.get('report_data'):
                    render_report_viewer()
                else:
                    st.info("📋 Results will appear here once processing is complete")
        else:
            render_welcome_screen()

def render_control_panel():
    st.subheader("🎛️ Agent Control")
    
    sender_email = st.text_input(
        "📧 Email Source", 
        value="wamitinewton@gmail.com",
        help="Email address to fetch claims from"
    )
    
    if not st.session_state.get('processing'):
        if st.button("🚀 Start Claims Processing", type="primary", use_container_width=True):
            start_processing(sender_email)
        
        if st.button("🔄 Reset Session", use_container_width=True):
            reset_session_state()
            st.rerun()
    else:
        st.button("⏸️ Processing...", disabled=True, use_container_width=True)
        
        if st.button("🛑 Stop Processing", type="secondary", use_container_width=True):
            stop_processing()
    
    with st.expander("⚙️ Advanced Settings"):
        st.checkbox("Enable Real-time Updates", value=True, disabled=True)
        st.checkbox("Show Tool Execution Details", value=True, key="show_tools")
        st.checkbox("Show Analysis Results", value=True, key="show_analysis")
        
        update_frequency = st.slider("Update Frequency (ms)", 100, 2000, 500)
        st.session_state.update_frequency = update_frequency

def render_quick_stats():
    st.markdown("### 📊 Quick Stats")
    
    progress = st.session_state.get('progress', 0.0)
    current_stage = st.session_state.get('current_stage', 'Ready')
    tool_history = st.session_state.get('tool_history', [])
    analysis_results = st.session_state.get('analysis_results', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Progress", f"{progress:.1f}%")
        st.metric("Current Stage", current_stage)
    
    with col2:
        st.metric("Tools Executed", len(tool_history))
        st.metric("Analyses Complete", len(analysis_results))
    
    if st.session_state.get('start_time'):
        duration = datetime.now() - st.session_state.start_time
        st.metric("Processing Time", f"{duration.seconds}s")
    
    if analysis_results:
        risk_levels = [r.get('risk_level', 'LOW') for r in analysis_results]
        high_risk = risk_levels.count('HIGH')
        if high_risk > 0:
            st.error(f"⚠️ {high_risk} High Risk Items")

def render_analytics_tab():
    if st.session_state.get('progress_data'):
        render_progress_timeline()
    
    if st.session_state.get('completed_stages'):
        render_stage_duration_chart()
    
    if st.session_state.get('tool_history'):
        render_tool_analytics()

def render_tool_analytics():
    st.subheader("🛠️ Tool Execution Analytics")
    
    tool_history = st.session_state.get('tool_history', [])
    
    if not tool_history:
        st.info("No tool execution data available yet...")
        return
    
    tool_counts = {}
    for tool in tool_history:
        tool_name = tool.get('tool_name', 'Unknown')
        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Most Used Tools**")
        sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)
        for tool_name, count in sorted_tools[:5]:
            st.markdown(f"• {tool_name}: {count} executions")
    
    with col2:
        st.markdown("**Execution Status**")
        status_counts = {'completed': 0, 'failed': 0, 'executing': 0}
        for tool in tool_history:
            status = tool.get('status', 'unknown')
            if status in status_counts:
                status_counts[status] += 1
        
        for status, count in status_counts.items():
            if count > 0:
                if status == 'completed':
                    st.success(f"✅ Completed: {count}")
                elif status == 'failed':
                    st.error(f"❌ Failed: {count}")
                else:
                    st.info(f"🔄 Executing: {count}")

def render_welcome_screen():
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h2>🤖 AI-Powered Claims Processing Agent</h2>
        <p style="font-size: 18px; color: #666; margin-bottom: 30px;">
            Advanced reinsurance claims analysis with real-time monitoring
        </p>
        
        <div style="display: flex; justify-content: space-around; margin: 40px 0;">
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 10px;">📧</div>
                <h4>Email Processing</h4>
                <p>Automatically fetches and analyzes claims emails</p>
            </div>
            
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 10px;">🔍</div>
                <h4>Smart Analysis</h4>
                <p>AI-powered fraud detection and compliance checks</p>
            </div>
            
            <div style="text-align: center;">
                <div style="font-size: 48px; margin-bottom: 10px;">📊</div>
                <h4>Real-time Reports</h4>
                <p>Comprehensive analysis reports with recommendations</p>
            </div>
        </div>
        
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin: 20px 0;">
            <h4>🚀 Ready to Start</h4>
            <p>Click the "Start Claims Processing" button to begin automated analysis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def start_processing(sender_email: str = "wamitinewton@gmail.com"):
    st.session_state.processing = True
    st.session_state.completed = False
    st.session_state.start_time = datetime.now()
    st.session_state.progress_data = []
    st.session_state.current_stage = "Initializing..."
    st.session_state.stage_message = "Starting claims processing..."
    st.session_state.progress = 0.0
    st.session_state.tool_history = []
    st.session_state.analysis_results = []
    st.session_state.completed_stages = []
    
    st.success("🚀 Claims processing started! Watch the real-time progress above.")
    
    def run_processing():
        try:
            client = WebSocketClient()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(client.start_processing_with_websocket(sender_email))
                
                if result.get("success"):
                    st.session_state.processing = False
                    st.session_state.completed = True
                    st.session_state.report_data = result.get("results", {})
                    st.session_state.processing_result = result
                    st.session_state.progress = 100.0
                    st.session_state.current_stage = "Completed"
                    st.session_state.stage_message = "Claims processing completed successfully!"
                else:
                    st.session_state.processing = False
                    st.session_state.current_stage = "Failed"
                    st.session_state.stage_message = f"Processing failed: {result.get('error', 'Unknown error')}"
                    
            finally:
                loop.close()
                
        except Exception as e:
            st.session_state.processing = False
            st.session_state.current_stage = "Error"
            st.session_state.stage_message = f"Error: {str(e)}"
    
    processing_thread = threading.Thread(target=run_processing)
    processing_thread.daemon = True
    processing_thread.start()
    
    st.rerun()

def stop_processing():
    st.session_state.processing = False
    st.session_state.current_stage = "Stopped"
    st.session_state.stage_message = "Processing stopped by user"
    st.warning("⏸️ Processing stopped by user")

if __name__ == "__main__":
    main()

auto_refresh_placeholder = st.empty()

if st.session_state.get('processing'):
    time.sleep(st.session_state.get('update_frequency', 500) / 1000)
    st.rerun()