import os

import streamlit as st

from ui.components.ui import status_pill, metric_card, stat_row, empty_state, pdf_frame
from ui.theme import tone_key_for_recommendation, tone_key_for_risk


def render_report_viewer():
    st.header("Claims Analysis Report")

    report_data = st.session_state.run.final_result

    if not report_data:
        empty_state("No report data available for this run.", icon="📋")
        return

    tab1, tab2, tab3 = st.tabs(["Summary", "Full Report", "Details"])

    with tab1:
        render_summary_tab(report_data)

    with tab2:
        render_full_report_tab(report_data)

    with tab3:
        render_details_tab(report_data)


def render_summary_tab(report_data):
    recommendation = report_data.get('overall_recommendation', 'Unknown')
    fraud_risk = report_data.get('fraud_risk_level', 'Unknown')
    critical_issues = report_data.get('critical_issues', [])

    stat_row([
        ("Final Recommendation", recommendation, tone_key_for_recommendation(recommendation)),
        ("Fraud Risk", fraud_risk, tone_key_for_risk(fraud_risk)),
        ("Critical Issues", str(len(critical_issues)), "danger" if critical_issues else "success"),
    ])

    st.markdown("---")

    if critical_issues:
        st.subheader("Critical Issues")
        for issue in critical_issues:
            status_pill(issue, tone="danger")

    next_steps = report_data.get('next_steps', [])
    if next_steps:
        st.subheader("Next Steps")
        for step in next_steps:
            st.markdown(f"- {step}")


def render_full_report_tab(report_data):
    report_generated = report_data.get('report_generated', {})
    pdf_path = report_generated.get('pdf_path')

    if pdf_path and os.path.exists(pdf_path):
        st.subheader("PDF Report")

        with open(pdf_path, "rb") as file:
            pdf_bytes = file.read()

        pdf_frame(pdf_bytes)

        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_path),
            mime="application/pdf"
        )
    else:
        empty_state("No PDF report was generated for this run.", icon="📄")

    html_content = report_generated.get('html_content')
    if html_content:
        with st.expander("View HTML Report"):
            st.components.v1.html(html_content, height=800, scrolling=True)

    executive_summary = report_generated.get('executive_summary')
    if executive_summary:
        st.subheader("Executive Summary")
        st.text_area("Summary", executive_summary, height=200, disabled=True)


def render_details_tab(report_data):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Document Processing")
        doc_processing = report_data.get('document_processing', {})

        metric_card("Files Processed", str(doc_processing.get('files_processed', 0)))
        metric_card("Email Completeness", str(doc_processing.get('email_completeness', 'Unknown')))

        missing_docs = doc_processing.get('missing_documents', [])
        if missing_docs:
            st.markdown("**Missing Documents:**")
            for doc in missing_docs:
                st.markdown(f"- {doc}")

    with col2:
        st.subheader("Analysis Summary")
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
            status_pill(check_name, tone="success" if completed else "danger")

    st.markdown("---")

    st.subheader("Processing Metadata")
    metadata = report_data.get('processing_metadata', {})
    agent_statuses = metadata.get('agent_statuses', {})
    completed_agents = sum(1 for status in agent_statuses.values() if status == 'completed')

    stat_row([
        ("Email Sender", str(metadata.get('email_sender', 'N/A')), "neutral"),
        ("Processing Agents", str(metadata.get('total_processing_agents', 0)), "neutral"),
        ("Completed Agents", f"{completed_agents}/{len(agent_statuses)}", "neutral"),
    ])

    if st.button("View Raw Data"):
        st.json(report_data)
