"""Frozen real-time contract (WORKFLOW.md Phase 0 / Appendix A).

Stage names and their expected terminal progress, taken directly from the
agents that emit them (agents/master_agent.py, document_agent.py,
analysis_agent.py, report_agent.py). Do not add stages here that the agents
don't actually emit - this is a mirror of the code, not aspirational.
"""

# agent_id suffix -> (display name, ordered stage list)
LANES = {
    "master": (
        "Master",
        [
            ("initialization", "Initialization", 2.0),
            ("document_processing", "Document Processing", 5.0),
            ("claims_analysis", "Claims Analysis", 35.0),
            ("report_generation", "Report Generation", 70.0),
            ("finalization", "Finalization", 95.0),
            ("completion", "Completion", 100.0),
        ],
    ),
    "document": (
        "Document Agent",
        [
            ("initialization", "Initialization", 5.0),
            ("email_connection", "Email Connection", 10.0),
            ("attachment_download", "Attachment Download", 20.0),
            ("document_preprocessing", "Document Preprocessing", 35.0),
            ("email_analysis", "Email Analysis", 45.0),
            ("document_processing", "Document Processing", 60.0),
            ("data_validation", "Data Validation", 80.0),
            ("completion", "Completion", 100.0),
        ],
    ),
    "analysis": (
        "Analysis Agent",
        [
            ("initialization", "Initialization", 5.0),
            ("document_query", "Document Query", 15.0),
            ("fraud_detection", "Fraud Detection", 25.0),
            ("exclusion_check", "Exclusion Check", 35.0),
            ("amount_reconciliation", "Amount Reconciliation", 45.0),
            ("date_validation", "Date Validation", 55.0),
            ("duplicate_check", "Duplicate Check", 65.0),
            ("compliance_validation", "Compliance Validation", 75.0),
            ("final_assessment", "Final Assessment", 85.0),
            ("completion", "Completion", 100.0),
        ],
    ),
    "report": (
        "Report Agent",
        [
            ("initialization", "Initialization", 5.0),
            ("template_preparation", "Template Preparation", 15.0),
            ("data_compilation", "Data Compilation", 25.0),
            ("html_generation", "HTML Generation", 45.0),
            ("pdf_conversion", "PDF Conversion", 65.0),
            ("summary_generation", "Summary Generation", 80.0),
            ("completion", "Completion", 100.0),
        ],
    ),
}

LANE_ORDER = ["master", "document", "analysis", "report"]


def lane_for_agent_id(agent_id: str) -> str:
    """Demux an AgentUpdate's agent_id into one of LANE_ORDER.

    Sub-agent ids are always `<root_agent_id>_document|_analysis|_report`
    (agents/master_agent.py `_run_*` methods) - the suffix alone is enough to
    tell lanes apart without the UI needing to already know the master's id.
    """
    for suffix in ("document", "analysis", "report"):
        if agent_id.endswith(f"_{suffix}"):
            return suffix
    return "master"


def root_agent_id(agent_id: str) -> str:
    """Strip a sub-agent suffix to get the run's master agent_id."""
    for suffix in ("_document", "_analysis", "_report"):
        if agent_id.endswith(suffix):
            return agent_id[: -len(suffix)]
    return agent_id
