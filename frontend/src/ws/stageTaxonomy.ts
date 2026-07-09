export const LANE_ORDER = ["master", "document", "analysis", "report"] as const;
export type Lane = (typeof LANE_ORDER)[number];

export interface StageDef {
  key: string;
  label: string;
  progress: number;
}

export const LANES: Record<Lane, { label: string; stages: StageDef[] }> = {
  master: {
    label: "Master",
    stages: [
      { key: "initialization", label: "Initialization", progress: 2.0 },
      { key: "document_processing", label: "Document Processing", progress: 5.0 },
      { key: "claims_analysis", label: "Claims Analysis", progress: 35.0 },
      { key: "report_generation", label: "Report Generation", progress: 70.0 },
      { key: "finalization", label: "Finalization", progress: 95.0 },
      { key: "completion", label: "Completion", progress: 100.0 },
    ],
  },
  document: {
    label: "Document Agent",
    stages: [
      { key: "initialization", label: "Initialization", progress: 5.0 },
      { key: "email_connection", label: "Email Connection", progress: 10.0 },
      { key: "attachment_download", label: "Attachment Download", progress: 20.0 },
      { key: "document_preprocessing", label: "Document Preprocessing", progress: 35.0 },
      { key: "email_analysis", label: "Email Analysis", progress: 45.0 },
      { key: "document_processing", label: "Document Processing", progress: 60.0 },
      { key: "data_validation", label: "Data Validation", progress: 80.0 },
      { key: "completion", label: "Completion", progress: 100.0 },
    ],
  },
  analysis: {
    label: "Analysis Agent",
    stages: [
      { key: "initialization", label: "Initialization", progress: 5.0 },
      { key: "document_query", label: "Document Query", progress: 15.0 },
      { key: "fraud_detection", label: "Fraud Detection", progress: 25.0 },
      { key: "exclusion_check", label: "Exclusion Check", progress: 35.0 },
      { key: "amount_reconciliation", label: "Amount Reconciliation", progress: 45.0 },
      { key: "date_validation", label: "Date Validation", progress: 55.0 },
      { key: "duplicate_check", label: "Duplicate Check", progress: 65.0 },
      { key: "compliance_validation", label: "Compliance Validation", progress: 75.0 },
      { key: "final_assessment", label: "Final Assessment", progress: 85.0 },
      { key: "completion", label: "Completion", progress: 100.0 },
    ],
  },
  report: {
    label: "Report Agent",
    stages: [
      { key: "initialization", label: "Initialization", progress: 5.0 },
      { key: "template_preparation", label: "Template Preparation", progress: 15.0 },
      { key: "data_compilation", label: "Data Compilation", progress: 25.0 },
      { key: "html_generation", label: "HTML Generation", progress: 45.0 },
      { key: "pdf_conversion", label: "PDF Conversion", progress: 65.0 },
      { key: "summary_generation", label: "Summary Generation", progress: 80.0 },
      { key: "completion", label: "Completion", progress: 100.0 },
    ],
  },
};

const SUFFIXES: Lane[] = ["document", "analysis", "report"];

export function laneForAgentId(agentId: string): Lane {
  for (const suffix of SUFFIXES) {
    if (agentId.endsWith(`_${suffix}`)) return suffix;
  }
  return "master";
}

export function rootAgentId(agentId: string): string {
  for (const suffix of SUFFIXES) {
    if (agentId.endsWith(`_${suffix}`)) return agentId.slice(0, -(suffix.length + 1));
  }
  return agentId;
}
