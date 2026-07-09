export interface ProcessingRecord {
  agent_id: string;
  sender_email: string;
  start_time: string; // ISO 8601
  end_time: string; // ISO 8601
  duration_seconds?: number;
  status: "COMPLETED" | "FAILED";
  recommendation?: string;
  critical_issues_count?: number;
  report_path?: string;
  error?: string;
}

export interface PipelineStats {
  total_processed: number;
  successful: number;
  failed: number;
  success_rate: number;
  active_agents: number;
  average_processing_time: number;
  recommendations_breakdown: Record<string, number>;
  last_processing: ProcessingRecord | null;
}

export interface MasterResult {
  master_agent_id: string;
  processing_status: "COMPLETED";
  overall_recommendation: "APPROVE" | "REJECT" | "REVIEW";
  fraud_risk_level: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";
  document_processing: {
    status: string;
    files_processed: number;
    email_completeness: string;
    missing_documents: string[];
  };
  analysis_summary: {
    fraud_analysis_completed: boolean;
    exclusion_check_completed: boolean;
    reconciliation_completed: boolean;
    date_validation_completed: boolean;
    duplicate_check_completed: boolean;
    compliance_validation_completed: boolean;
  };
  critical_issues: string[];
  report_generated: {
    pdf_path: string | null;
    generation_timestamp: string;
    executive_summary: string;
  };
  next_steps: string[];
  processing_metadata: {
    email_sender: string;
    email_subject: string;
    total_processing_agents: number;
    agent_statuses: Record<string, string>;
  };
}

export type AgentStatus = "initialized" | "processing" | "completed" | "failed" | "paused";

export interface AgentUpdate {
  agent_id: string;
  timestamp: string;
  status: AgentStatus;
  stage: string;
  message: string;
  progress: number;
  data: Record<string, unknown> | null;
  error: string | null;
}

export interface StartProcessingResponse {
  started: boolean;
  sender_email?: string;
  reason?: string;
}
