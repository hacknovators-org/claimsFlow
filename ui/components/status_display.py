import streamlit as st
from datetime import datetime

def render_status_display():
    st.subheader("📊 Processing Status")
    
    if st.session_state.get('start_time'):
        duration = datetime.now() - st.session_state.start_time
        st.metric("Processing Time", f"{duration.seconds}s")
    
    current_stage = st.session_state.get('current_stage', 'Ready')
    progress = st.session_state.get('progress', 0.0)
    
    st.metric("Current Stage", current_stage)
    st.metric("Progress", f"{progress:.1f}%")
    
    if st.session_state.get('processing'):
        st.info("🔄 Agent is actively processing...")
    elif st.session_state.get('completed'):
        result = st.session_state.get('processing_result', {})
        recommendation = result.get('results', {}).get('overall_recommendation', 'Unknown')
        
        if recommendation == "APPROVE":
            st.success(f"✅ Processing Complete: {recommendation}")
        elif recommendation == "REJECT":
            st.error(f"❌ Processing Complete: {recommendation}")
        else:
            st.warning(f"⚠️ Processing Complete: {recommendation}")
    else:
        st.info("⭐ Ready to start processing")
    
    if st.session_state.get('report_data'):
        critical_issues = st.session_state.report_data.get('critical_issues', [])
        if critical_issues:
            st.warning(f"⚠️ {len(critical_issues)} Critical Issues Found")
        
        fraud_risk = st.session_state.report_data.get('fraud_risk_level', 'Unknown')
        if fraud_risk == 'HIGH':
            st.error(f"🚨 Fraud Risk: {fraud_risk}")
        elif fraud_risk == 'MEDIUM':
            st.warning(f"⚡ Fraud Risk: {fraud_risk}")
        elif fraud_risk == 'LOW':
            st.success(f"✅ Fraud Risk: {fraud_risk}")
        else:
            st.info(f"❓ Fraud Risk: {fraud_risk}")