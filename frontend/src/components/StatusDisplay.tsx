import { useMutation } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { api } from "../api/client";
import { useRunStore, type RunView } from "../store/runStore";
import { toneForRecommendation, toneForRisk } from "../theme/tokens";
import { StatRow } from "./ui/StatRow";
import { Button } from "./ui/button";

export function StatusDisplay({ view }: { view: RunView }) {
  const message = useRunStore((s) => s.message);
  const error = useRunStore((s) => s.error);
  const master = useRunStore((s) => s.laneUpdates.master);
  const finalResult = useRunStore((s) => s.finalResult);
  const startNewRun = useRunStore((s) => s.startNewRun);

  const retryMutation = useMutation({
    mutationFn: () => api.startProcessing(),
    onSuccess: (result) => {
      if (result.started) startNewRun(result.sender_email);
    },
  });

  if (view === "failed") {
    return (
      <div className="flex items-start gap-3 rounded-xl border border-danger-border bg-danger-bg p-4">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-danger-fg" strokeWidth={2} />
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-danger-fg">Processing failed</h3>
          <p className="mt-1 text-sm text-danger-fg/90">{error ?? "Something went wrong before the run could finish."}</p>
          <Button variant="danger" className="mt-3" onClick={() => retryMutation.mutate()} disabled={retryMutation.isPending}>
            Try again
          </Button>
        </div>
      </div>
    );
  }

  if (view === "completed" && finalResult) {
    return (
      <div className="rounded-xl border border-neutral-border bg-surface p-4 shadow-soft">
        <StatRow
          items={[
            {
              label: "Recommendation",
              value: finalResult.overall_recommendation,
              tone: toneForRecommendation(finalResult.overall_recommendation),
            },
            {
              label: "Fraud Risk",
              value: finalResult.fraud_risk_level,
              tone: toneForRisk(finalResult.fraud_risk_level),
            },
            { label: "Critical Issues", value: finalResult.critical_issues.length },
          ]}
        />
      </div>
    );
  }

  const finalRecommendation = master?.data?.final_recommendation as string | undefined;

  return (
    <div className="rounded-xl border border-neutral-border bg-surface p-4 shadow-soft">
      <p className="flex items-center gap-2 text-sm text-ink">
        <span className="h-2 w-2 animate-pulse rounded-full bg-info-fg" />
        {message ?? "Starting…"}
      </p>
      {finalRecommendation && (
        <div className="mt-3">
          <StatRow
            items={[
              {
                label: "Recommendation",
                value: finalRecommendation,
                tone: toneForRecommendation(finalRecommendation),
              },
            ]}
          />
        </div>
      )}
    </div>
  );
}
