import streamlit as st
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_progress_tracker():
    st.subheader("🔄 Real-time Agent Processing")
    
    current_progress = st.session_state.get('progress', 0.0)
    current_stage = st.session_state.get('current_stage', 'Ready')
    stage_message = st.session_state.get('stage_message', 'Waiting to start...')
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_main_progress(current_progress, current_stage, stage_message)
    
    with col2:
        render_stage_indicators(current_progress)
    
    if st.session_state.get('processing') or st.session_state.get('tool_history'):
        render_tool_execution_panel()
    
    if st.session_state.get('analysis_results'):
        render_analysis_results()

def render_main_progress(progress, stage, message):
    progress_container = st.container()
    
    with progress_container:
        progress_fig = create_circular_progress(progress)
        st.plotly_chart(progress_fig, use_container_width=True, key="main_progress")
        
        st.markdown(f"""
        <div style="text-align: center; margin-top: -50px;">
            <h3 style="color: #1f77b4; margin-bottom: 5px;">{stage}</h3>
            <p style="color: #666; font-size: 14px; margin: 0;">{message}</p>
        </div>
        """, unsafe_allow_html=True)

def create_circular_progress(progress):
    fig = go.Figure(data=[
        go.Pie(
            values=[progress, 100-progress],
            hole=0.7,
            marker_colors=['#1f77b4', '#e6e6e6'],
            textinfo='none',
            showlegend=False,
            hoverinfo='skip'
        )
    ])
    
    fig.add_annotation(
        text=f"<b>{progress:.1f}%</b>",
        x=0.5, y=0.5,
        font_size=32,
        font_color="#1f77b4",
        showarrow=False
    )
    
    fig.update_layout(
        height=250,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def render_stage_indicators(current_progress):
    stages = [
        ("Initialization", "🔧", 0, 10),
        ("Document Processing", "📄", 10, 35),
        ("Claims Analysis", "🔍", 35, 75),
        ("Report Generation", "📊", 75, 95),
        ("Completion", "✅", 95, 100)
    ]
    
    st.markdown("**Processing Stages**")
    
    for stage_name, icon, start_progress, end_progress in stages:
        if current_progress >= end_progress:
            status_color = "#28a745"
            status_icon = "✅"
            bg_color = "#d4edda"
        elif current_progress >= start_progress:
            status_color = "#007bff"
            status_icon = "🔄"
            bg_color = "#cce5ff"
        else:
            status_color = "#6c757d"
            status_icon = "⏳"
            bg_color = "#f8f9fa"
        
        st.markdown(f"""
        <div style="
            background-color: {bg_color}; 
            padding: 8px; 
            border-radius: 5px; 
            margin-bottom: 5px;
            border-left: 4px solid {status_color};
        ">
            <div style="display: flex; align-items: center;">
                <span style="margin-right: 8px;">{status_icon}</span>
                <span style="font-weight: bold; color: {status_color};">{stage_name}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_tool_execution_panel():
    st.markdown("---")
    st.subheader("🛠️ Tool Execution Monitor")
    
    current_tool = st.session_state.get('current_tool', '')
    tool_status = st.session_state.get('tool_status', '')
    tool_description = st.session_state.get('tool_description', '')
    tool_history = st.session_state.get('tool_history', [])
    
    if current_tool and tool_status == 'executing':
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**Current Tool:**")
            if tool_status == 'executing':
                st.markdown("🔄 **Executing**")
            elif tool_status == 'completed':
                st.markdown("✅ **Completed**")
            else:
                st.markdown("❌ **Failed**")
        
        with col2:
            st.markdown(f"**{current_tool}**")
            st.caption(tool_description)
            
            if tool_status == 'executing':
                st.progress(0.5)
    
    if tool_history:
        with st.expander("🔍 Tool Execution History", expanded=False):
            for i, tool in enumerate(reversed(tool_history[-10:])):
                timestamp = tool.get('timestamp', '')
                tool_name = tool.get('tool_name', '')
                status = tool.get('status', '')
                description = tool.get('description', '')
                
                if status == 'completed':
                    status_icon = "✅"
                    status_color = "#28a745"
                elif status == 'failed':
                    status_icon = "❌"
                    status_color = "#dc3545"
                else:
                    status_icon = "🔄"
                    status_color = "#007bff"
                
                st.markdown(f"""
                <div style="
                    padding: 8px; 
                    border-left: 3px solid {status_color};
                    margin-bottom: 8px;
                    background-color: rgba(0,0,0,0.02);
                ">
                    <div style="display: flex; align-items: center; margin-bottom: 4px;">
                        <span style="margin-right: 8px;">{status_icon}</span>
                        <strong style="color: {status_color};">{tool_name}</strong>
                    </div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 2px;">{description}</div>
                    <div style="font-size: 10px; color: #999;">{timestamp}</div>
                </div>
                """, unsafe_allow_html=True)

def render_analysis_results():
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    analysis_results = st.session_state.get('analysis_results', [])
    
    if not analysis_results:
        st.info("No analysis results yet...")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        for result in analysis_results[-5:]:
            analysis_type = result.get('type', '')
            analysis_result = result.get('result', '')
            risk_level = result.get('risk_level', 'LOW')
            timestamp = result.get('timestamp', '')
            
            if risk_level == 'HIGH':
                risk_color = "#dc3545"
                risk_icon = "🚨"
            elif risk_level == 'MEDIUM':
                risk_color = "#ffc107"
                risk_icon = "⚠️"
            else:
                risk_color = "#28a745"
                risk_icon = "✅"
            
            st.markdown(f"""
            <div style="
                border: 1px solid {risk_color};
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                background-color: rgba(0,0,0,0.02);
            ">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="margin-right: 8px;">{risk_icon}</span>
                    <strong style="color: {risk_color};">{analysis_type.replace('_', ' ').title()}</strong>
                    <span style="margin-left: auto; font-size: 12px; color: #666;">{risk_level}</span>
                </div>
                <div style="font-size: 14px; color: #333;">{analysis_result}</div>
                <div style="font-size: 10px; color: #999; margin-top: 4px;">{timestamp}</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        render_risk_summary(analysis_results)

def render_risk_summary(analysis_results):
    risk_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    
    for result in analysis_results:
        risk_level = result.get('risk_level', 'LOW')
        risk_counts[risk_level] += 1
    
    total_analyses = len(analysis_results)
    
    if total_analyses > 0:
        st.markdown("**Risk Summary**")
        
        for risk_level, count in risk_counts.items():
            if count > 0:
                percentage = (count / total_analyses) * 100
                
                if risk_level == 'HIGH':
                    color = "#dc3545"
                    icon = "🚨"
                elif risk_level == 'MEDIUM':
                    color = "#ffc107"
                    icon = "⚠️"
                else:
                    color = "#28a745"
                    icon = "✅"
                
                st.markdown(f"""
                <div style="
                    display: flex; 
                    align-items: center; 
                    padding: 6px;
                    margin-bottom: 4px;
                ">
                    <span style="margin-right: 8px;">{icon}</span>
                    <span style="color: {color}; font-weight: bold;">{risk_level}:</span>
                    <span style="margin-left: auto;">{count} ({percentage:.1f}%)</span>
                </div>
                """, unsafe_allow_html=True)

def render_progress_timeline():
    progress_data = st.session_state.get('progress_data', [])
    
    if not progress_data:
        return
    
    st.markdown("---")
    st.subheader("📈 Progress Timeline")
    
    timestamps = [datetime.fromisoformat(p['timestamp'].replace('Z', '+00:00')) for p in progress_data]
    progress_values = [p['progress'] for p in progress_data]
    stages = [p['stage'] for p in progress_data]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=progress_values,
        mode='lines+markers',
        name='Progress',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{text}</b><br>Progress: %{y:.1f}%<br>Time: %{x}<extra></extra>',
        text=stages
    ))
    
    fig.update_layout(
        title="Processing Progress Over Time",
        xaxis_title="Time",
        yaxis_title="Progress (%)",
        height=300,
        yaxis=dict(range=[0, 100]),
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_stage_duration_chart():
    completed_stages = st.session_state.get('completed_stages', [])
    
    if not completed_stages:
        return
    
    st.markdown("---")
    st.subheader("⏱️ Stage Duration Analysis")
    
    stages = [s['stage'] for s in completed_stages]
    durations = [s['duration'] for s in completed_stages]
    success_statuses = [s['success'] for s in completed_stages]
    
    colors = ['#28a745' if success else '#dc3545' for success in success_statuses]
    
    fig = go.Figure(data=[
        go.Bar(
            x=stages,
            y=durations,
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>Duration: %{y:.2f}s<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Stage Execution Times",
        xaxis_title="Stage",
        yaxis_title="Duration (seconds)",
        height=300,
        margin=dict(t=50, b=100, l=50, r=50),
        xaxis={'tickangle': 45}
    )
    
    st.plotly_chart(fig, use_container_width=True)