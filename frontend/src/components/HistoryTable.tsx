import { format } from "date-fns";
import { FileText } from "lucide-react";
import type { ProcessingRecord } from "../api/types";
import { api } from "../api/client";
import { toneForRecommendation } from "../theme/tokens";
import { StatusPill } from "./ui/StatusPill";
import { EmptyState } from "./ui/EmptyState";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

function formatTimestamp(iso: string) {
  try {
    return format(new Date(iso), "MMM d, yyyy HH:mm:ss");
  } catch {
    return iso;
  }
}

export function HistoryTable({ history }: { history: ProcessingRecord[] }) {
  if (history.length === 0) {
    return <EmptyState message="No processing runs yet. Once a claim finishes, it will show up here." />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Agent ID</TableHead>
          <TableHead>Sender</TableHead>
          <TableHead>Started</TableHead>
          <TableHead>Duration</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Recommendation</TableHead>
          <TableHead>Critical Issues</TableHead>
          <TableHead>Report</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...history].reverse().map((record) => (
          <TableRow key={record.agent_id}>
            <TableCell className="font-mono text-xs text-muted">{record.agent_id}</TableCell>
            <TableCell>{record.sender_email}</TableCell>
            <TableCell className="font-mono text-xs text-muted">{formatTimestamp(record.start_time)}</TableCell>
            <TableCell className="font-mono text-xs">
              {record.duration_seconds != null ? `${record.duration_seconds.toFixed(1)}s` : "—"}
            </TableCell>
            <TableCell>
              <StatusPill label={record.status} tone={record.status === "COMPLETED" ? "success" : "danger"} />
            </TableCell>
            <TableCell>
              {record.recommendation ? (
                <StatusPill label={record.recommendation} tone={toneForRecommendation(record.recommendation)} />
              ) : (
                "—"
              )}
            </TableCell>
            <TableCell>{record.critical_issues_count ?? "—"}</TableCell>
            <TableCell>
              {record.status === "COMPLETED" ? (
                <a
                  href={api.reportPdfUrl(record.agent_id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 font-medium text-brand hover:underline"
                >
                  <FileText className="h-3.5 w-3.5" strokeWidth={2} />
                  View PDF
                </a>
              ) : (
                "—"
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
