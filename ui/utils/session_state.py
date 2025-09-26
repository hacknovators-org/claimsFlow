import streamlit as st
from datetime import datetime

def initialize_session_state():
    """Initialize all session state variables for real-time UI"""
    
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
    
    if 'stage_message' not in st.session_state:
        st.session_state.stage_message = "Waiting to start..."
    
    if 'progress_data' not in st.session_state:
        st.session_state.progress_data = []
    
    if 'report_data' not in st.session_state:
        st.session_state.report_data = None
    
    if 'processing_result' not in st.session_state:
        st.session_state.processing_result = None
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = None
    
    if 'current_tool' not in st.session_state:
        st.session_state.current_tool = ""
    
    if 'tool_status' not in st.session_state:
        st.session_state.tool_status = ""
    
    if 'tool_description' not in st.session_state:
        st.session_state.tool_description = ""
    
    if 'tool_history' not in st.session_state:
        st.session_state.tool_history = []
    
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    if 'completed_stages' not in st.session_state:
        st.session_state.completed_stages = []
    
    if 'websocket_connected' not in st.session_state:
        st.session_state.websocket_connected = False
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    if 'update_frequency' not in st.session_state:
        st.session_state.update_frequency = 500
    
    if 'show_tools' not in st.session_state:
        st.session_state.show_tools = True
    
    if 'show_analysis' not in st.session_state:
        st.session_state.show_analysis = True

def reset_session_state():
    """Reset session state for new processing"""
    st.session_state.processing = False
    st.session_state.completed = False
    st.session_state.start_time = None
    st.session_state.progress = 0.0
    st.session_state.current_stage = "Ready"
    st.session_state.stage_message = "Waiting to start..."
    st.session_state.progress_data = []
    st.session_state.report_data = None
    st.session_state.processing_result = None
    st.session_state.last_update = None
    st.session_state.current_tool = ""
    st.session_state.tool_status = ""
    st.session_state.tool_description = ""
    st.session_state.tool_history = []
    st.session_state.analysis_results = []
    st.session_state.completed_stages = []

def update_progress(progress: float, stage: str, message: str):
    """Update progress state"""
    st.session_state.progress = progress
    st.session_state.current_stage = stage
    st.session_state.stage_message = message
    st.session_state.last_update = datetime.now()
    
    st.session_state.progress_data.append({
        'timestamp': datetime.now().isoformat(),
        'progress': progress,
        'stage': stage,
        'message': message
    })

def update_tool_execution(tool_name: str, description: str, status: str = "executing"):
    """Update tool execution state"""
    st.session_state.current_tool = tool_name
    st.session_state.tool_description = description
    st.session_state.tool_status = status
    
    st.session_state.tool_history.append({
        'timestamp': datetime.now().isoformat(),
        'tool_name': tool_name,
        'description': description,
        'status': status
    })

def add_analysis_result(analysis_type: str, result: str, risk_level: str = "LOW"):
    """Add analysis result to session state"""
    st.session_state.analysis_results.append({
        'timestamp': datetime.now().isoformat(),
        'type': analysis_type,
        'result': result,
        'risk_level': risk_level
    })

def complete_stage(stage: str, duration: float, success: bool = True):
    """Mark a stage as completed"""
    st.session_state.completed_stages.append({
        'timestamp': datetime.now().isoformat(),
        'stage': stage,
        'duration': duration,
        'success': success
    })

def get_processing_stats():
    """Get current processing statistics"""
    return {
        'progress': st.session_state.get('progress', 0.0),
        'current_stage': st.session_state.get('current_stage', 'Ready'),
        'tools_executed': len(st.session_state.get('tool_history', [])),
        'analyses_completed': len(st.session_state.get('analysis_results', [])),
        'stages_completed': len(st.session_state.get('completed_stages', [])),
        'processing_time': (datetime.now() - st.session_state.start_time).total_seconds() if st.session_state.get('start_time') else 0,
        'websocket_connected': st.session_state.get('websocket_connected', False)
    }