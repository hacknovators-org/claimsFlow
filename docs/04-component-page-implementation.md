# 04 — Component & Page Implementation Guide

Status: **Planning — implementation not yet started.**
Depends on: [03-frontend-project-setup.md](./03-frontend-project-setup.md)
(store, WS hook, API client, theme tokens must exist first).

---

## 1. Component inventory

1:1 mapping from the deleted Streamlit components to their React
replacements. Build these against **static/mock data first** (no live WS
dependency), so each is independently reviewable/testable before wiring live
data — same phased approach the Streamlit component library used.

| Old (`ui/components/...`) | New (`src/components/...`) | Notes |
|---|---|---|
| `ui/status_pill.py` | `ui/StatusPill.tsx` | `<StatusPill label tone />` — renders label with the tone's fg/bg/border from theme tokens. Replaces every hand-rolled `if risk == "HIGH": st.error()` branch. |
| `ui/metric_card.py` | `ui/MetricCard.tsx` | `<MetricCard label value />` — simple bordered stat tile. |
| (stat_row helper) | `ui/StatRow.tsx` | `<StatRow items={[{label, value, tone}]} />` — horizontal flex of `MetricCard`s or pills, used on Dashboard idle view and History page header stats. |
| `ui/stage_lane.py` | `ui/StageLane.tsx` | `<StageLane lane="document" update={AgentUpdate|undefined} />` — renders one agent's stage list + progress bar from `LANES[lane]` (§03) and the latest update for that lane. Undefined update ⇒ render all stages as not-yet-reached. |
| `ui/empty_state.py` | `ui/EmptyState.tsx` | `<EmptyState message icon />` — dashed-border placeholder, used for "no runs yet" and "no report generated." |
| `ui/skeleton_block.py` | `ui/SkeletonBlock.tsx` | `<SkeletonBlock />` — shimmer placeholder shown between "run started" and "first WS message received." |
| `ui/pdf_frame.py` | (inline in `ReportViewer.tsx`) | No dedicated component needed — just an `<iframe src={api.reportPdfUrl(agentId)}>`, since the backend now serves the PDF by URL (`02-backend-api-contract.md` §2.2) instead of Streamlit's base64-embed-from-bytes approach. |
| `components/header.py` | `Header.tsx` | App title + live WS connection indicator (`connecting`/`open`/`reconnecting` from `useWebSocket`, §03 §5) — new: Streamlit never surfaced connection state explicitly. |
| (sidebar controls in `ui/main.py`) | `Sidebar.tsx` | Start/Stop button, wired to TanStack Query mutations over `api.startProcessing`/`api.stopAgent`. |
| `components/report_viewer.py` | `ReportViewer.tsx` | Tabs: Summary / Full Report / Details — use shadcn `Tabs`. |
| `components/progress_tracker.py` | `ProgressTracker.tsx` | Renders 4 `StageLane`s in `LANE_ORDER` (§03 §6), one per lane, reading from `runStore.laneUpdates`. **No `simulate_progress()` equivalent** — there is nothing to port here; progress is 100% driven by real `AgentUpdate.progress` values, never fabricated client-side. |
| `components/status_display.py` | `StatusDisplay.tsx` | Top summary bar during running/completed/failed: current stage message, recommendation/risk pills once available, and — new — an explicit failed-state branch rendering `runStore.error` (the deleted Streamlit version never had a distinct failed treatment). |
| `components/history_view.py` | `HistoryTable.tsx` | shadcn `Table` + stat row, backed by `api.getHistory()`/`api.getStatus()` via TanStack Query. |

---

## 2. Component specs

### `StatusPill`

```tsx
type Tone = "success" | "warning" | "danger" | "info" | "neutral";
function StatusPill({ label, tone }: { label: string; tone: Tone }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-sm font-semibold
                       bg-${tone}-bg text-${tone}-fg border border-${tone}-border`}>
      {label}
    </span>
  );
}
```
(Tailwind's JIT compiler needs these tone class names to appear literally
somewhere it can statically scan — either write them out per-tone in a
lookup object, or add the five tone/property combinations to Tailwind's
`safelist` in `tailwind.config.ts`, since `bg-${tone}-bg` as a runtime
template string won't be picked up by static scanning otherwise.)

### `StageLane`

Props: `lane: Lane`, `update: AgentUpdate | undefined`.
Renders `LANES[lane].label` as a heading, then a small progress bar sized to
`update?.progress ?? 0`, then the stage list with the current stage
highlighted and prior stages checked off (`stage` index lookup against
`LANES[lane].stages`). If `update.status === "failed"`, render the stage row
in `danger` tone with `update.error` beneath it instead of the message.

### `ReportViewer`

Props: `result: MasterResult`, `agentId: string`.

- **Summary tab**: `StatRow` of Recommendation / Fraud Risk / Critical Issues
  count (tones via `toneForRecommendation`/`toneForRisk`, §03 §8), critical
  issues list as `StatusPill`s (`danger` tone), next steps as a plain list —
  direct port of `report_viewer.py:30` `render_summary_tab`.
- **Full Report tab**: `<iframe src={api.reportPdfUrl(agentId)} className="w-full h-[80vh]" />`
  plus a `<a href={api.reportPdfUrl(agentId)} download>Download PDF</a>`. If
  `report_generated.pdf_path` is null (no PDF was generated for this run),
  render `EmptyState` instead — mirrors `report_viewer.py:59`'s
  `os.path.exists` guard, except the existence check now lives server-side
  in the `/report.pdf` route (`02` §2.2), so the frontend only needs to
  check `result.report_generated.pdf_path !== null` before rendering the
  iframe.
- **Details tab**: two-column layout — document processing metrics
  (`MetricCard` x2 + missing docs list) and analysis summary checklist
  (`StatusPill` per check, success/danger by boolean) — direct port of
  `report_viewer.py:87` `render_details_tab`. Processing metadata stat row +
  a collapsible raw-JSON view (shadcn `Collapsible` or a plain
  `<details>/<pre>`) replaces the Streamlit `st.json` debug button.

### `StatusDisplay`

Props: `view: RunView`, `store: RunStore` (or pass the specific fields
needed). Branches:
- `running`: current stage message (`store.message`), recommendation/risk
  pills once analysis lane has reported them via `update.data` (only
  `completion` events currently attach a `data` payload —
  `agents/master_agent.py:37` attaches `final_recommendation` on the
  `completion` stage, so don't expect these pills before that point).
- `completed`: recommendation + risk pills from the fetched result.
- `failed` **(new)**: a distinct red-toned panel showing `store.error`
  verbatim, plus a "Try again" button that calls `api.startProcessing()`
  again. This state didn't exist as a distinct branch in the deleted
  Streamlit `status_display.py` — building it is an explicit improvement,
  not a like-for-like port.

---

## 3. Pages

### `Dashboard.tsx` (`/`)

State-driven view switch on `useRunStore().view()` — this **is** the ported
`ui/main.py` routing logic (`view == "idle" | "running" | "completed" |
"failed"`), just as a React component tree instead of a Streamlit
if/elif chain:

```tsx
function Dashboard() {
  const view = useRunStore((s) => s.view());
  const { data: status } = useQuery({ queryKey: ["status"], queryFn: api.getStatus, enabled: view === "idle" });

  return (
    <>
      <Sidebar />
      {view === "idle" && <IdleView stats={status} />}
      {view === "running" && <RunningView />}
      {view === "completed" && <CompletedView />}
      {view === "failed" && <StatusDisplay view="failed" />}
    </>
  );
}
```

- **`IdleView`**: `StatRow` of total runs / success rate / last
  recommendation from `PipelineStats` (port of `ui/main.py:94`
  `render_idle_view`), or `EmptyState` if `total_processed === 0`.
- **`RunningView`**: `StatusDisplay` + `ProgressTracker`. No polling interval
  needed here — updates arrive via the WS push, not a fragment-style
  re-render loop (Streamlit needed `st.fragment(run_every=1.0)` to
  work around its full-script rerun model; React's normal re-render on
  state change replaces that mechanism entirely — this is a real
  simplification, not just a port).
- **`CompletedView`**: fetch the result once via TanStack Query
  (`useQuery(["result", agentId], () => api.getResult(agentId), { enabled: !resultFetched })`)
  and set it on the store (mirrors `ui/main.py:135` `_ensure_result_fetched`'s
  fetch-once guard), then render `StatusDisplay` + `ReportViewer`.

### `Sidebar.tsx`

```tsx
function Sidebar() {
  const view = useRunStore((s) => s.view());
  const rootAgentId = useRunStore((s) => s.rootAgentId);
  const startNewRun = useRunStore((s) => s.startNewRun);

  const startMutation = useMutation({
    mutationFn: api.startProcessing,
    onSuccess: (result) => {
      if (!result.started) return; // surface result.reason in a toast — don't silently no-op
      startNewRun(result.sender_email);
    },
  });
  const stopMutation = useMutation({ mutationFn: () => api.stopAgent(rootAgentId!) });

  const idle = view === "idle" || view === "completed" || view === "failed";
  return idle
    ? <button onClick={() => startMutation.mutate(undefined)} disabled={startMutation.isPending}>Start Claims Processing</button>
    : <>
        <button disabled>Processing…</button>
        <button onClick={() => stopMutation.mutate()}>Stop Processing</button>
      </>;
}
```

Surface `startMutation.data?.reason` (the `"A processing run is already
active"` rejection from `routes/processing.py:20`) as a toast/inline
warning, not a silent failure — this is the one place the frontend must
handle the backend's single-active-run constraint explicitly (flagged as a
risk in [01](./01-architecture-decision.md) §8).

### `History.tsx` (`/history`)

Direct port of `ui/components/history_view.py`: `StatRow` (total runs /
success rate / active agents) + `HistoryTable` fed by
`useQuery(["history"], () => api.getHistory())`. Poll every 5-10s while this
page is mounted (`refetchInterval`) since, unlike the Dashboard, this page
has no WS-driven live updates of its own — it's a periodic-refresh table, not
a broadcast consumer.

---

## 4. Data flow summary

```
AgentUpdate (WS) ──▶ WebSocketProvider ──▶ runStore.applyUpdate()
                                              │
                                              ▼
                                     runStore.view() (derived)
                                              │
                    ┌─────────────┬───────────┼───────────┐
                    ▼             ▼           ▼           ▼
                 IdleView    RunningView  CompletedView  Failed panel
                              (StageLane ×4 from laneUpdates)
```

REST (`api.*`) is only used for: triggering/stopping a run, fetching
snapshots (`status`, `history`), and fetching the final result once a run
completes. Everything about an *in-progress* run's live state comes from the
WS stream — never poll `/processing/status` during an active run just to
approximate progress; that would reintroduce the exact "fake progress bar"
problem (`simulate_progress()`) the original Streamlit migration explicitly
eliminated.
