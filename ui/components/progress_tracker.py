import streamlit as st
import time

def render_progress_tracker():
    st.subheader("🔄 Agent Processing Stages")
    
    stages = [
        ("Initialization", "🔧", "Setting up processing agents"),
        ("Document Processing", "📄", "Fetching and analyzing email attachments"),
        ("Claims Analysis", "🔍", "Running comprehensive claims validation"),
        ("Report Generation", "📊", "Creating detailed analysis report"),
        ("Completion", "✅", "Finalizing results")
    ]
    
    current_progress = st.session_state.get('progress', 0.0)
    current_stage = st.session_state.get('current_stage', 'Ready')
    
    progress_bar = st.progress(current_progress / 100.0)
    
    st.markdown(f"**Current Stage:** {current_stage}")
    
    for i, (stage_name, icon, description) in enumerate(stages):
        stage_progress = (i + 1) * 20
        
        if current_progress >= stage_progress:
            status = "✅"
            color = "green"
        elif current_progress >= (stage_progress - 20):
            status = "🔄"
            color = "blue"
        else:
            status = "⏳"
            color = "gray"
        
        col1, col2, col3 = st.columns([1, 3, 6])
        
        with col1:
            st.markdown(f"<span style='color: {color}'>{status}</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"{icon} **{stage_name}**")
        
        with col3:
            st.markdown(f"*{description}*")
    
    if st.session_state.get('processing'):
        simulate_progress()

def simulate_progress():
    if 'progress' not in st.session_state:
        st.session_state.progress = 0.0
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_update > 1:
        if st.session_state.progress < 95:
            increment = min(2.5, 95 - st.session_state.progress)
            st.session_state.progress += increment
            
            if st.session_state.progress < 20:
                st.session_state.current_stage = "Initializing agents..."
            elif st.session_state.progress < 40:
                st.session_state.current_stage = "Processing documents..."
            elif st.session_state.progress < 70:
                st.session_state.current_stage = "Analyzing claims..."
            elif st.session_state.progress < 90:
                st.session_state.current_stage = "Generating report..."
            else:
                st.session_state.current_stage = "Finalizing..."
            
            st.session_state.last_update = current_time
            
            time.sleep(0.1)
            st.rerun()