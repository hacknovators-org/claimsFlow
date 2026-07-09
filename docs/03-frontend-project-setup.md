# 03 — Frontend Project Setup

Status: **Planning — implementation not yet started.**
Scope: new `frontend/` directory at the repo root, sitting alongside the
existing Python backend. Depends on
[02-backend-api-contract.md](./02-backend-api-contract.md) for the API/WS
shapes this scaffold is built against.

---

## 1. Scaffold

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom @tanstack/react-query zustand date-fns
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn@latest init
```

Add to root `.gitignore` (if not already covered by a broad `node_modules`
rule): `frontend/node_modules/`, `frontend/dist/`.

---

## 2. Folder structure

```
frontend/
  src/
    api/
      client.ts          # typed fetch wrapper over /processing/*
      types.ts            # PipelineStats, ProcessingRecord, MasterResult, AgentUpdate
    ws/
      useWebSocket.ts      # reconnecting WS hook, ports ws_subscriber.py
      stageTaxonomy.ts     # LANES, lane_for_agent_id, root_agent_id — ports stage_taxonomy.py
    store/
      runStore.ts          # Zustand store, ports session_state.py's RunState
    theme/
      tokens.ts            # ports theme.py's TONES/SPACING
    components/
      ui/                  # shadcn primitives (Button, Tabs, Table, Dialog) + our own:
        StatusPill.tsx
        MetricCard.tsx
        StatRow.tsx
        StageLane.tsx
        EmptyState.tsx
        SkeletonBlock.tsx
      Header.tsx
      Sidebar.tsx
      ReportViewer.tsx
      ProgressTracker.tsx
      StatusDisplay.tsx
      HistoryTable.tsx
    pages/
      Dashboard.tsx         # "/" — idle/running/completed/failed
      History.tsx           # "/history"
    App.tsx                 # router + persistent WS connection provider
    main.tsx
  .env.development           # VITE_API_BASE_URL=http://localhost:8000
  .env.production             # VITE_API_BASE_URL= (same-origin, leave empty — see doc 05)
  tailwind.config.ts
```

This is a near 1:1 rename of the deleted `ui/` package's responsibilities:
`ui/theme.py` → `theme/tokens.ts`, `ui/utils/stage_taxonomy.py` →
`ws/stageTaxonomy.ts`, `ui/utils/session_state.py` → `store/runStore.ts`,
`ui/servicesui/processing_client.py` → `api/client.ts`,
`ui/servicesui/ws_subscriber.py` → `ws/useWebSocket.ts`,
`ui/components/*` → `components/*`. Nothing here is a new design — it's the
same architecture ported to a real component framework.

---

## 3. Env config

```
# .env.development
VITE_API_BASE_URL=http://localhost:8000
```

```
# .env.production
VITE_API_BASE_URL=
```

`VITE_API_BASE_URL=""` in prod means "same origin as the page" — correct
once the SPA is served by FastAPI itself (§05). If a split deploy is used
instead, set the real API origin here at build time.

---

## 4. API client (`src/api/client.ts`)

Direct port of `ui/servicesui/processing_client.py`, typed:

```ts
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
    request<{ started: boolean; sender_email?: string; reason?: string }>(
      `/processing/start${senderEmail ? `?sender_email=${encodeURIComponent(senderEmail)}` : ""}`,
      { method: "POST" }
    ),
  getStatus: () => request<PipelineStats>("/processing/status"),
  getHistory: (limit = 50) => request<{ history: ProcessingRecord[] }>(`/processing/history?limit=${limit}`),
  getResult: (agentId: string) => request<MasterResult>(`/processing/result/${agentId}`),
  stopAgent: (agentId: string) => request<{ stopped: boolean }>(`/processing/stop/${agentId}`, { method: "POST" }),
  reportPdfUrl: (agentId: string) => `${API_BASE_URL}/processing/result/${agentId}/report.pdf`,
};
```

Wire `startProcessing`/`stopAgent` as TanStack Query **mutations**, and
`getStatus`/`getHistory` as **queries** (`getHistory` polled every few
seconds only on the `/history` page — no need to poll it from the dashboard,
which gets its live data from the WS stream instead).

---

## 5. WebSocket hook (`src/ws/useWebSocket.ts`)

Port of `ui/servicesui/ws_subscriber.py`'s reconnect-with-backoff loop, using
the browser's native `WebSocket` instead of the `websockets` library:

```ts
import { useEffect, useRef, useState } from "react";
import { wsUrl } from "../api/client";
import type { AgentUpdate } from "../api/types";

export type ConnectionState = "connecting" | "open" | "reconnecting" | "closed";

export function useWebSocket(onMessage: (update: AgentUpdate) => void) {
  const [state, setState] = useState<ConnectionState>("connecting");
  const stopped = useRef(false);

  useEffect(() => {
    stopped.current = false;
    let socket: WebSocket | null = null;
    let retryDelay = 1000;

    function connect() {
      if (stopped.current) return;
      setState((prev) => (prev === "connecting" ? "connecting" : "reconnecting"));
      socket = new WebSocket(wsUrl());

      socket.onopen = () => {
        retryDelay = 1000;
        setState("open");
      };
      socket.onmessage = (event) => {
        try {
          onMessage(JSON.parse(event.data));
        } catch {
          console.warn("Dropped malformed WS message", event.data);
        }
      };
      socket.onclose = () => {
        if (stopped.current) return;
        setState("reconnecting");
        setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 15000);
      };
      socket.onerror = () => socket?.close();
    }

    connect();
    return () => {
      stopped.current = true;
      setState("closed");
      socket?.close();
    };
  }, [onMessage]);

  return state;
}
```

Call this **once**, at `App.tsx` level (a context provider), not per-page —
same "one connection for the app's lifetime" principle the deleted
`get_or_create_subscriber` singleton enforced per Streamlit session.
Exponential backoff (1s → 2s → 4s … capped at 15s) avoids hammering the
server if it's down; this is stricter than the Streamlit version's flat 2s
retry, since a browser tab can be left open indefinitely.

---

## 6. Stage taxonomy (`src/ws/stageTaxonomy.ts`)

Direct port of `ui/utils/stage_taxonomy.py` — see
[02-backend-api-contract.md](./02-backend-api-contract.md) §1.7 for the
frozen stage list this mirrors:

```ts
export const LANE_ORDER = ["master", "document", "analysis", "report"] as const;
export type Lane = (typeof LANE_ORDER)[number];

export const LANES: Record<Lane, { label: string; stages: [string, string, number][] }> = {
  master: {
    label: "Master",
    stages: [
      ["initialization", "Initialization", 2.0],
      ["document_processing", "Document Processing", 5.0],
      ["claims_analysis", "Claims Analysis", 35.0],
      ["report_generation", "Report Generation", 70.0],
      ["finalization", "Finalization", 95.0],
      ["completion", "Completion", 100.0],
    ],
  },
  document: {
    label: "Document Agent",
    stages: [
      ["initialization", "Initialization", 5.0],
      ["email_connection", "Email Connection", 10.0],
      ["attachment_download", "Attachment Download", 20.0],
      ["document_preprocessing", "Document Preprocessing", 35.0],
      ["email_analysis", "Email Analysis", 45.0],
      ["document_processing", "Document Processing", 60.0],
      ["data_validation", "Data Validation", 80.0],
      ["completion", "Completion", 100.0],
    ],
  },
  analysis: {
    label: "Analysis Agent",
    stages: [
      ["initialization", "Initialization", 5.0],
      ["document_query", "Document Query", 15.0],
      ["fraud_detection", "Fraud Detection", 25.0],
      ["exclusion_check", "Exclusion Check", 35.0],
      ["amount_reconciliation", "Amount Reconciliation", 45.0],
      ["date_validation", "Date Validation", 55.0],
      ["duplicate_check", "Duplicate Check", 65.0],
      ["compliance_validation", "Compliance Validation", 75.0],
      ["final_assessment", "Final Assessment", 85.0],
      ["completion", "Completion", 100.0],
    ],
  },
  report: {
    label: "Report Agent",
    stages: [
      ["initialization", "Initialization", 5.0],
      ["template_preparation", "Template Preparation", 15.0],
      ["data_compilation", "Data Compilation", 25.0],
      ["html_generation", "HTML Generation", 45.0],
      ["pdf_conversion", "PDF Conversion", 65.0],
      ["summary_generation", "Summary Generation", 80.0],
      ["completion", "Completion", 100.0],
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
```

---

## 7. Run store (`src/store/runStore.ts`)

Direct port of `ui/utils/session_state.py`'s `RunState` — the `view` getter
and `apply_update` reducer logic are ported **verbatim**, since that state
machine was already carefully worked out (new-run detection, stale-broadcast
rejection, terminal-state handling) and shouldn't be redesigned mid-port:

```ts
import { create } from "zustand";
import { laneForAgentId, rootAgentId, type Lane } from "../ws/stageTaxonomy";
import type { AgentUpdate } from "../api/types";

export type RunView = "idle" | "running" | "completed" | "failed";

interface RunStore {
  started: boolean;
  rootAgentId: string | null;
  senderEmail: string | null;
  laneUpdates: Partial<Record<Lane, AgentUpdate>>;
  finalResult: unknown | null;
  resultFetched: boolean;
  error: string | null;
  message: string | null;

  view: () => RunView;
  startNewRun: (senderEmail?: string) => void;
  applyUpdate: (update: AgentUpdate) => void;
  setFinalResult: (result: unknown) => void;
}

export const useRunStore = create<RunStore>((set, get) => ({
  started: false,
  rootAgentId: null,
  senderEmail: null,
  laneUpdates: {},
  finalResult: null,
  resultFetched: false,
  error: null,
  message: null,

  view: () => {
    const master = get().laneUpdates.master;
    if (!master) return get().started ? "running" : "idle";
    if (master.status === "failed" || master.status === "paused") return "failed";
    if (master.status === "completed") return "completed";
    return "running";
  },

  startNewRun: (senderEmail) =>
    set({
      started: true,
      senderEmail: senderEmail ?? null,
      rootAgentId: null,
      laneUpdates: {},
      finalResult: null,
      resultFetched: false,
      error: null,
      message: null,
    }),

  applyUpdate: (update) => {
    const lane = laneForAgentId(update.agent_id);
    const incomingRoot = rootAgentId(update.agent_id);
    const state = get();

    const isNewRunStart =
      lane === "master" &&
      incomingRoot !== state.rootAgentId &&
      update.status !== "completed" &&
      update.status !== "failed";

    if (isNewRunStart) {
      set({
        rootAgentId: incomingRoot,
        laneUpdates: {},
        finalResult: null,
        resultFetched: false,
        error: null,
      });
    }

    if (get().rootAgentId !== null && incomingRoot !== get().rootAgentId) {
      return; // stale broadcast from a run this client isn't tracking
    }

    set((s) => ({
      laneUpdates: { ...s.laneUpdates, [lane]: update },
      ...(lane === "master"
        ? {
            message: update.message,
            error: update.status === "failed" ? update.error : s.error,
          }
        : {}),
    }));
  },

  setFinalResult: (result) => set({ finalResult: result, resultFetched: true }),
}));
```

Wire `applyUpdate` as the `onMessage` callback passed to `useWebSocket`
(§5), called once at the app root so every page shares one store instance —
this replaces Streamlit's `st.session_state.run` singleton-per-session with
Zustand's module-level singleton-per-tab, which is the equivalent concept in
a React SPA.

---

## 8. Theme tokens (`src/theme/tokens.ts` + `tailwind.config.ts`)

Port `ui/theme.py`'s `TONES`/`SPACING` maps directly into Tailwind's
`theme.extend`, so components reference `bg-success-bg text-success-fg
border-success-border` etc. instead of ad hoc hex values — same "one
semantic system" principle the Streamlit theme layer enforced:

```ts
// tailwind.config.ts (excerpt)
export default {
  theme: {
    extend: {
      colors: {
        brand: "#1D4E5F",
        success: { fg: "#0F5132", bg: "#E8F5EE", border: "#A8D5BC" },
        danger:  { fg: "#7A1F1F", bg: "#FBEAEA", border: "#E8B4B4" },
        warning: { fg: "#7A5A00", bg: "#FFF6DE", border: "#E8D48A" },
        info:    { fg: "#1D4E5F", bg: "#EAF2F4", border: "#B7D3DA" },
        neutral: { fg: "#4B5563", bg: "#F4F6F7", border: "#D8DEE1" },
      },
    },
  },
};
```

```ts
// src/theme/tokens.ts
export const RECOMMENDATION_TONE: Record<string, string> = {
  APPROVE: "success", REJECT: "danger", REVIEW: "warning",
};
export const RISK_TONE: Record<string, string> = {
  LOW: "success", MEDIUM: "warning", HIGH: "danger",
};
export const AGENT_STATUS_TONE: Record<string, string> = {
  initialized: "neutral", processing: "info", completed: "success",
  failed: "danger", paused: "neutral",
};

export const toneForRecommendation = (v: string) => RECOMMENDATION_TONE[v?.toUpperCase()] ?? "neutral";
export const toneForRisk = (v: string) => RISK_TONE[v?.toUpperCase()] ?? "neutral";
export const toneForAgentStatus = (v: string) => AGENT_STATUS_TONE[v?.toLowerCase()] ?? "neutral";
```

---

## 9. Routing (`src/App.tsx`)

```tsx
<QueryClientProvider client={queryClient}>
  <BrowserRouter>
    <WebSocketProvider>{/* mounts useWebSocket once, feeds runStore */}
      <Header />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </WebSocketProvider>
  </BrowserRouter>
</QueryClientProvider>
```

Next: [04-component-page-implementation.md](./04-component-page-implementation.md)
specs every component and page listed in §2's folder structure.
