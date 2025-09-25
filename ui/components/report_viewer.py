import streamlit as st
import base64
import os
import json

def render_report_viewer():
    st.header("📋 Claims Analysis Report")
    
    report_data = st.session_state.get('report_data', {})
    
    if not report_data:
        st.warning("No report data available")
        return
    
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "📄 Full Report", "🔍 Details"])
    
    with tab1:
        render_summary_tab(report_data)
    
    with tab2:
        render_full_report_tab(report_data)
    
    with tab3:
        render_details_tab(report_data)

def render_summary_tab(report_data):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        recommendation = report_data.get('overall_recommendation', 'Unknown')
        if recommendation == 'APPROVE':
            st.success(f"**Final Recommendation**\n\n✅ {recommendation}")
        elif recommendation == 'REJECT':
            st.error(f"**Final Recommendation**\n\n❌ {recommendation}")
        else:
            st.warning(f"**Final Recommendation**\n\n⚠️ {recommendation}")
    
    with col2:
        fraud_risk = report_data.get('fraud_risk_level', 'Unknown')
        if fraud_risk == 'HIGH':
            st.error(f"**Fraud Risk**\n\n🚨 {fraud_risk}")
        elif fraud_risk == 'MEDIUM':
            st.warning(f"**Fraud Risk**\n\n⚡ {fraud_risk}")
        elif fraud_risk == 'LOW':
            st.success(f"**Fraud Risk**\n\n✅ {fraud_risk}")
        else:
            st.info(f"**Fraud Risk**\n\n❓ {fraud_risk}")
    
    with col3:
        critical_issues = report_data.get('critical_issues', [])
        if critical_issues:
            st.error(f"**Critical Issues**\n\n⚠️ {len(critical_issues)} Found")
        else:
            st.success(f"**Critical Issues**\n\n✅ None Found")
    
    st.markdown("---")
    
    if critical_issues:
        st.subheader("🚨 Critical Issues")
        for issue in critical_issues:
            st.error(f"• {issue}")
    
    next_steps = report_data.get('next_steps', [])
    if next_steps:
        st.subheader("📋 Next Steps")
        for step in next_steps:
            st.info(f"• {step}")

def render_full_report_tab(report_data):
    report_generated = report_data.get('report_generated', {})
    pdf_path = report_generated.get('pdf_path')
    
    if pdf_path and os.path.exists(pdf_path):
        st.subheader("📄 PDF Report")
        
        with open(pdf_path, "rb") as file:
            pdf_bytes = file.read()
            b64 = base64.b64encode(pdf_bytes).decode()
            
            pdf_display = f'''
            <iframe src="data:application/pdf;base64,{b64}" 
                    width="100%" height="800" 
                    style="border: 1px solid #ccc;">
            </iframe>
            '''
            
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_path),
                mime="application/pdf"
            )
    
    html_content = report_generated.get('html_content')
    if html_content:
        with st.expander("🌐 View HTML Report"):
            st.components.v1.html(html_content, height=800, scrolling=True)
    
    executive_summary = report_generated.get('executive_summary')
    if executive_summary:
        st.subheader("📝 Executive Summary")
        st.text_area("Summary", executive_summary, height=200, disabled=True)

def render_details_tab(report_data):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📧 Document Processing")
        doc_processing = report_data.get('document_processing', {})
        
        st.metric("Files Processed", doc_processing.get('files_processed', 0))
        st.metric("Email Completeness", doc_processing.get('email_completeness', 'Unknown'))
        
        missing_docs = doc_processing.get('missing_documents', [])
        if missing_docs:
            st.warning("Missing Documents:")
            for doc in missing_docs:
                st.write(f"• {doc}")
    
    with col2:
        st.subheader("🔍 Analysis Summary")
        analysis = report_data.get('analysis_summary', {})
        
        checks = [
            ("Fraud Analysis", analysis.get('fraud_analysis_completed', False)),
            ("Exclusion Check", analysis.get('exclusion_check_completed', False)),
            ("Reconciliation", analysis.get('reconciliation_completed', False)),
            ("Date Validation", analysis.get('date_validation_completed', False)),
            ("Duplicate Check", analysis.get('duplicate_check_completed', False)),
            ("Compliance", analysis.get('compliance_validation_completed', False))
        ]
        
        for check_name, completed in checks:
            if completed:
                st.success(f"✅ {check_name}")
            else:
                st.error(f"❌ {check_name}")
    
    st.markdown("---")
    
    st.subheader("📊 Processing Metadata")
    metadata = report_data.get('processing_metadata', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Email Sender", metadata.get('email_sender', 'N/A'))
    
    with col2:
        st.metric("Processing Agents", metadata.get('total_processing_agents', 0))
    
    with col3:
        agent_statuses = metadata.get('agent_statuses', {})
        completed_agents = sum(1 for status in agent_statuses.values() if status == 'completed')
        st.metric("Completed Agents", f"{completed_agents}/{len(agent_statuses)}")
    
    if st.button("📋 View Raw Data"):
        st.json(report_data)