import type {
  MasterResult,
  PipelineStats,
  ProcessingRecord,
  StartProcessingResponse,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export function wsUrl(): string {
  const base = API_BASE_URL || window.location.origin;
  return base.replace(/^http/, "ws") + "/ws";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  startProcessing: (senderEmail?: string) =>
    request<StartProcessingResponse>(
      `/processing/start${senderEmail ? `?sender_email=${encodeURIComponent(senderEmail)}` : ""}`,
      { method: "POST" }
    ),
  getStatus: () => request<PipelineStats>("/processing/status"),
  getHistory: (limit = 50) =>
    request<{ history: ProcessingRecord[] }>(`/processing/history?limit=${limit}`),
  getResult: (agentId: string) => request<MasterResult>(`/processing/result/${agentId}`),
  stopAgent: (agentId: string) =>
    request<{ stopped: boolean }>(`/processing/stop/${agentId}`, { method: "POST" }),
  reportPdfUrl: (agentId: string) => `${API_BASE_URL}/processing/result/${agentId}/report.pdf`,
};
