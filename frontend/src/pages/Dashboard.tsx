import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useRunStore } from "../store/runStore";
import type { PipelineStats } from "../api/types";
import { Sidebar } from "../components/Sidebar";
import { StatusDisplay } from "../components/StatusDisplay";
import { ProgressTracker } from "../components/ProgressTracker";
import { ReportViewer } from "../components/ReportViewer";
import { StatRow } from "../components/ui/StatRow";
import { EmptyState } from "../components/ui/EmptyState";
import { toneForRecommendation } from "../theme/tokens";

function IdleView({ stats }: { stats: PipelineStats | undefined }) {
  if (!stats || stats.total_processed === 0) {
    return <EmptyState message="No runs yet. Start claims processing to pull the latest claim from the inbox and watch it move through the pipeline." />;
  }

  const lastRecommendation = stats.last_processing?.recommendation;

  return (
    <StatRow
      items={[
        { label: "Total Runs", value: stats.total_processed },
        { label: "Success Rate", value: `${stats.success_rate.toFixed(0)}%` },
        ...(lastRecommendation
          ? [{ label: "Last Recommendation", value: lastRecommendation, tone: toneForRecommendation(lastRecommendation) }]
          : []),
      ]}
    />
  );
}

function RunningView() {
  return (
    <div className="space-y-5">
      <StatusDisplay view="running" />
      <ProgressTracker />
    </div>
  );
}

function CompletedView() {
  const rootAgentId = useRunStore((s) => s.rootAgentId);
  const resultFetched = useRunStore((s) => s.resultFetched);
  const finalResult = useRunStore((s) => s.finalResult);
  const setFinalResult = useRunStore((s) => s.setFinalResult);

  const { data } = useQuery({
    queryKey: ["result", rootAgentId],
    queryFn: () => api.getResult(rootAgentId!),
    enabled: Boolean(rootAgentId) && !resultFetched,
  });

  useEffect(() => {
    if (data) setFinalResult(data);
  }, [data, setFinalResult]);

  return (
    <div className="space-y-5">
      <StatusDisplay view="completed" />
      {finalResult && rootAgentId && <ReportViewer result={finalResult} agentId={rootAgentId} />}
    </div>
  );
}

const VIEW_COPY: Record<string, { title: string; subtitle: string }> = {
  idle: { title: "Pipeline", subtitle: "Waiting for the next claim." },
  running: { title: "Pipeline", subtitle: "Processing a claim in real time." },
  completed: { title: "Pipeline", subtitle: "Run finished — review the outcome below." },
  failed: { title: "Pipeline", subtitle: "The run stopped before it finished." },
};

export function Dashboard() {
  const view = useRunStore((s) => s.view());
  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: api.getStatus,
    enabled: view === "idle",
  });

  const copy = VIEW_COPY[view];

  return (
    <>
      <Sidebar />
      <main className="flex-1 p-6">
        <div className="mx-auto max-w-6xl">
          <div className="mb-6">
            <h1 className="font-display text-2xl font-semibold text-ink">{copy.title}</h1>
            <p className="mt-1 text-sm text-muted">{copy.subtitle}</p>
          </div>
          {view === "idle" && <IdleView stats={status} />}
          {view === "running" && <RunningView />}
          {view === "completed" && <CompletedView />}
          {view === "failed" && <StatusDisplay view="failed" />}
        </div>
      </main>
    </>
  );
}
