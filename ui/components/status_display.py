import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

def render_status_display():
    st.subheader("📊 Processing Status")
    
    render_main_metrics()
    render_connection_status()
    render_current_activity()
    
    if st.session_state.get('processing') or st.session_state.get('completed'):
        render_processing_summary()

def render_main_metrics():
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.get('start_time'):
            duration = datetime.now() - st.session_state.start_time
            st.metric("Processing Time", f"{duration.seconds}s")
        else:
            st.metric("Processing Time", "0s")
    
    with col2:
        current_stage = st.session_state.get('current_stage', 'Ready')
        progress = st.session_state.get('progress', 0.0)
        st.metric("Progress", f"{progress:.1f}%", f"{current_stage}")

def render_connection_status():
    websocket_connected = st.session_state.get('websocket_connected', False)
    
    if websocket_connected:
        st.success("🔗 WebSocket Connected - Real-time updates active")
    else:
        st.info("📡 WebSocket Disconnected - Using fallback mode")

def render_current_activity():
    if st.session_state.get('processing'):
        current_stage = st.session_state.get('current_stage', 'Processing')
        stage_message = st.session_state.get('stage_message', 'Working...')
        
        st.info(f"🔄 **{current_stage}**\n\n{stage_message}")
        
        current_tool = st.session_state.get('current_tool', '')
        tool_status = st.session_state.get('tool_status', '')
        
        if current_tool and tool_status == 'executing':
            tool_description = st.session_state.get('tool_description', '')
            st.markdown(f"""
            <div style="
                background-color: #e3f2fd;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #2196f3;
                margin: 10px 0;
            ">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 8px;">🛠️</span>
                    <strong>Executing: {current_tool}</strong>
                </div>
                <div style="font-size: 12px; color: #666; margin-top: 4px;">{tool_description}</div>
                <div style="margin-top: 8px;">
                    <div style="width: 100%; background-color: #e0e0e0; border-radius: 3px; height: 6px;">
                        <div style="width: 50%; height: 100%; background-color: #2196f3; border-radius: 3px; animation: pulse 1.5s infinite;"></div>
                    </div>
                </div>
            </div>
            
            <style>
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
            </style>
            """, unsafe_allow_html=True)
    
    elif st.session_state.get('completed'):
        result = st.session_state.get('processing_result', {})
        recommendation = result.get('results', {}).get('overall_recommendation', 'Unknown')
        
        if recommendation == "APPROVE":
            st.success(f"✅ **Processing Complete**\n\nRecommendation: **{recommendation}**")
        elif recommendation == "REJECT":
            st.error(f"❌ **Processing Complete**\n\nRecommendation: **{recommendation}**")
        else:
            st.warning(f"⚠️ **Processing Complete**\n\nRecommendation: **{recommendation}**")
    
    else:
        st.info("⭐ **Ready to Start**\n\nClick 'Start Claims Processing' to begin analysis")

def render_processing_summary():
    st.markdown("---")
    st.markdown("### 📈 Processing Summary")
    
    tool_history = st.session_state.get('tool_history', [])
    analysis_results = st.session_state.get('analysis_results', [])
    completed_stages = st.session_state.get('completed_stages', [])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tools Executed", len(tool_history))
        if tool_history:
            successful_tools = len([t for t in tool_history if t.get('status') == 'completed'])
            success_rate = (successful_tools / len(tool_history)) * 100
            st.metric("Tool Success Rate", f"{success_rate:.1f}%")
    
    with col2:
        st.metric("Analyses Complete", len(analysis_results))
        if analysis_results:
            high_risk = len([a for a in analysis_results if a.get('risk_level') == 'HIGH'])
            if high_risk > 0:
                st.metric("High Risk Items", high_risk, delta=high_risk, delta_color="inverse")
    
    with col3:
        st.metric("Stages Complete", len(completed_stages))
        if completed_stages:
            avg_duration = sum(s.get('duration', 0) for s in completed_stages) / len(completed_stages)
            st.metric("Avg Stage Time", f"{avg_duration:.2f}s")

def render_risk_indicators():
    analysis_results = st.session_state.get('analysis_results', [])
    
    if not analysis_results:
        return
    
    st.markdown("### ⚠️ Risk Assessment")
    
    risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    for result in analysis_results:
        risk_level = result.get('risk_level', 'LOW')
        if risk_level in risk_counts:
            risk_counts[risk_level] += 1
    
    total = sum(risk_counts.values())
    
    if total > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            high_pct = (risk_counts['HIGH'] / total) * 100
            if risk_counts['HIGH'] > 0:
                st.error(f"🚨 HIGH: {risk_counts['HIGH']} ({high_pct:.1f}%)")
            else:
                st.success(f"🚨 HIGH: 0 (0%)")
        
        with col2:
            medium_pct = (risk_counts['MEDIUM'] / total) * 100
            if risk_counts['MEDIUM'] > 0:
                st.warning(f"⚠️ MEDIUM: {risk_counts['MEDIUM']} ({medium_pct:.1f}%)")
            else:
                st.success(f"⚠️ MEDIUM: 0 (0%)")
        
        with col3:
            low_pct = (risk_counts['LOW'] / total) * 100
            st.success(f"✅ LOW: {risk_counts['LOW']} ({low_pct:.1f}%)")

def render_mini_progress_chart():
    progress_data = st.session_state.get('progress_data', [])
    
    if len(progress_data) < 2:
        return
    
    recent_data = progress_data[-20:]  # Last 20 data points
    
    timestamps = [datetime.fromisoformat(p['timestamp']) for p in recent_data]
    progress_values = [p['progress'] for p in recent_data]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=progress_values,
        mode='lines',
        name='Progress',
        line=dict(color='#1f77b4', width=2),
        fill='tonexty' if len(timestamps) > 1 else None
    ))
    
    fig.update_layout(
        height=150,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
        xaxis=dict(showticklabels=False),
        yaxis=dict(range=[0, 100], showticklabels=False),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    st.plotly_chart(fig, use_container_width=True, key="mini_progress")