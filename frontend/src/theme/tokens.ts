export type Tone = "success" | "warning" | "danger" | "info" | "neutral";

export const RECOMMENDATION_TONE: Record<string, Tone> = {
  APPROVE: "success",
  REJECT: "danger",
  REVIEW: "warning",
};

export const RISK_TONE: Record<string, Tone> = {
  LOW: "success",
  MEDIUM: "warning",
  HIGH: "danger",
};

export const AGENT_STATUS_TONE: Record<string, Tone> = {
  initialized: "neutral",
  processing: "info",
  completed: "success",
  failed: "danger",
  paused: "neutral",
};

export const toneForRecommendation = (v: string | undefined): Tone =>
  (v ? RECOMMENDATION_TONE[v.toUpperCase()] : undefined) ?? "neutral";

export const toneForRisk = (v: string | undefined): Tone =>
  (v ? RISK_TONE[v.toUpperCase()] : undefined) ?? "neutral";

export const toneForAgentStatus = (v: string | undefined): Tone =>
  (v ? AGENT_STATUS_TONE[v.toLowerCase()] : undefined) ?? "neutral";
