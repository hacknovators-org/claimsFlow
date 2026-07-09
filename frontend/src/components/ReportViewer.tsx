import { ChevronRight } from "lucide-react";
import type { MasterResult } from "../api/types";
import { api } from "../api/client";
import { toneForRecommendation, toneForRisk } from "../theme/tokens";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { StatRow } from "./ui/StatRow";
import { StatusPill } from "./ui/StatusPill";
import { MetricCard } from "./ui/MetricCard";
import { EmptyState } from "./ui/EmptyState";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";

const ANALYSIS_CHECK_LABELS: Record<string, string> = {
  fraud_analysis_completed: "Fraud Analysis",
  exclusion_check_completed: "Exclusion Check",
  reconciliation_completed: "Amount Reconciliation",
  date_validation_completed: "Date Validation",
  duplicate_check_completed: "Duplicate Check",
  compliance_validation_completed: "Compliance Validation",
};

export function ReportViewer({ result, agentId }: { result: MasterResult; agentId: string }) {
  const pdfUrl = api.reportPdfUrl(agentId);
  const hasPdf = Boolean(result.report_generated.pdf_path);

  return (
    <div className="rounded-xl border border-neutral-border bg-surface p-5 shadow-soft">
      <Tabs defaultValue="summary">
        <TabsList>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="report">Full Report</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
        </TabsList>

        <TabsContent value="summary">
          <div className="space-y-5">
            <StatRow
              items={[
                {
                  label: "Recommendation",
                  value: result.overall_recommendation,
                  tone: toneForRecommendation(result.overall_recommendation),
                },
                {
                  label: "Fraud Risk",
                  value: result.fraud_risk_level,
                  tone: toneForRisk(result.fraud_risk_level),
                },
                { label: "Critical Issues", value: result.critical_issues.length },
              ]}
            />

            {result.critical_issues.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Critical Issues</h4>
                <div className="flex flex-col gap-2">
                  {result.critical_issues.map((issue) => (
                    <StatusPill key={issue} label={issue} tone="danger" />
                  ))}
                </div>
              </div>
            )}

            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Next Steps</h4>
              <ul className="space-y-1.5 text-sm text-ink">
                {result.next_steps.map((step) => (
                  <li key={step} className="flex gap-2">
                    <ChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" strokeWidth={2.5} />
                    {step}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="report">
          {hasPdf ? (
            <div className="space-y-3">
              <a href={pdfUrl} download className="text-sm font-medium text-brand hover:underline">
                Download PDF
              </a>
              <iframe src={pdfUrl} title="Claims analysis report" className="h-[80vh] w-full rounded-lg border border-neutral-border" />
            </div>
          ) : (
            <EmptyState message="No report was generated for this run." />
          )}
        </TabsContent>

        <TabsContent value="details">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">Document Processing</h4>
              <div className="flex gap-3">
                <MetricCard label="Files Processed" value={result.document_processing.files_processed} />
                <MetricCard label="Email Completeness" value={result.document_processing.email_completeness} />
              </div>
              {result.document_processing.missing_documents.length > 0 && (
                <div>
                  <h5 className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Missing Documents</h5>
                  <ul className="list-inside list-disc space-y-1 text-sm text-ink">
                    {result.document_processing.missing_documents.map((doc) => (
                      <li key={doc}>{doc}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">Analysis Checklist</h4>
              <div className="flex flex-col gap-2">
                {Object.entries(ANALYSIS_CHECK_LABELS).map(([key, label]) => {
                  const checkDone = Boolean(result.analysis_summary[key as keyof typeof result.analysis_summary]);
                  return <StatusPill key={key} label={label} tone={checkDone ? "success" : "danger"} />;
                })}
              </div>
            </div>
          </div>

          <div className="mt-6">
            <StatRow
              items={[
                { label: "Sender", value: result.processing_metadata.email_sender },
                { label: "Subject", value: result.processing_metadata.email_subject },
                { label: "Agents", value: result.processing_metadata.total_processing_agents },
              ]}
            />
          </div>

          <Collapsible className="mt-5">
            <CollapsibleTrigger className="text-sm font-medium text-brand hover:underline">
              Raw result JSON
            </CollapsibleTrigger>
            <CollapsibleContent>
              <pre className="mt-2 max-h-96 overflow-auto rounded-lg bg-console p-3 font-mono text-xs text-console-fg">
                {JSON.stringify(result, null, 2)}
              </pre>
            </CollapsibleContent>
          </Collapsible>
        </TabsContent>
      </Tabs>
    </div>
  );
}
