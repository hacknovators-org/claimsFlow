import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { StatRow } from "../components/ui/StatRow";
import { HistoryTable } from "../components/HistoryTable";

const POLL_INTERVAL_MS = 7000;

export function History() {
  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: api.getStatus,
    refetchInterval: POLL_INTERVAL_MS,
  });
  const { data: historyData } = useQuery({
    queryKey: ["history"],
    queryFn: () => api.getHistory(),
    refetchInterval: POLL_INTERVAL_MS,
  });

  return (
    <main className="flex-1 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <h1 className="font-display text-2xl font-semibold text-ink">History</h1>
          <p className="mt-1 text-sm text-muted">Every claim the pipeline has processed, most recent first.</p>
        </div>
        {status && (
          <StatRow
            items={[
              { label: "Total Runs", value: status.total_processed },
              { label: "Success Rate", value: `${status.success_rate.toFixed(0)}%` },
              { label: "Active Agents", value: status.active_agents },
            ]}
          />
        )}
        <HistoryTable history={historyData?.history ?? []} />
      </div>
    </main>
  );
}
