# UI Refactor & Real-Time Sync — Workflow Plan

Status: **Planning only — no implementation yet.**
Scope: `ui/`, `websocket_manager.py`, `websocket_server.py`, `pipeline_singleton.py`, `pipeline_controller.py`, `main.py`, `run.py`.
Out of scope: agent/analysis logic (`agents/*`, `document_processing/*`, `services/*`), data models, DB schema.

---

## 1. Decision Record

**Decision: stay on Streamlit.** No migration to React/Next.js.

Rationale: single Python codebase, no new build pipeline/auth/deploy story, and Streamlit's ceiling (custom `config.toml` theming, HTML/CSS component injection, `st.fragment`, native `st.status`/`st.toast`) is high enough for an internal reinsurance ops tool once actually used correctly. This plan is written to get as close to that ceiling as Streamlit allows. If a future iteration still finds the visual ceiling insufficient, re-open this decision — don't silently drift toward a hybrid.

---

## 2. Current State Audit

Findings from reading the current code, not assumptions. Each one is a concrete defect this refactor must resolve.

### 2.1 Real-time sync is fundamentally disconnected

- The backend **already has** a fully-built real-time event system: every agent (`agents/master_agent.py`, `document_agent.py`, `analysis_agent.py`, `report_agent.py`) calls `self.send_update(stage, message, progress, data, error)` (`agents/base_agent.py:38`), which broadcasts a structured JSON `AgentUpdate` over `websocket_manager.broadcast()`.
- **The Streamlit UI never connects to it.** `ui/servicesui/websocket_client.py:14` instantiates a brand-new `ClaimsProcessingPipeline()` with **no `websocket_manager`** — so `send_update` calls silently no-op (`if self.websocket_manager:` guard, `agents/base_agent.py:57`). No events are ever broadcast for UI-triggered runs.
- `ui/main.py:69` calls this via `asyncio.run(client.start_processing_sync())`, which **blocks the entire Streamlit script thread** until the pipeline finishes. There is no live UI during a run — the whole app freezes.
- `ui/components/progress_tracker.py:49` (`simulate_progress()`) fakes the progress bar with a client-side timer (+2.5% every second, capped at 95%) that has **no relationship to actual backend state**. This is the direct cause of "changes do not sync in real time."

### 2.2 Three disconnected pipeline entrypoints

- `run.py` → `uvicorn main:app` (port from `.env` `PORT=8000`) — the FastAPI app that actually runs in production. It only mounts `routes/sms.py` and the APScheduler; **no WebSocket route is mounted on it at all.**
- `main.py` run directly (`python main.py`) — a separate asyncio entrypoint gated by `RUN_MODE` (`.env` has `RUN_MODE=standalone`). In `websocket` mode it starts a **standalone `websockets.serve()` process** (`websocket_server.py:139`) on a *different* port (default `8765`, but `.env` sets `WEBSOCKET_PORT=8785` — **these are already inconsistent**, confirming this path isn't exercised).
- `run_ui.py` → Streamlit — talks to neither of the above; spins up its own orphan pipeline (2.1).
- Net effect: SMS-triggered runs (`routes/sms.py` → `pipeline_singleton.pipeline`, which **does** have the real `websocket_manager` wired — `pipeline_singleton.py:4`) and UI-triggered runs use **different `ClaimsProcessingPipeline` instances**, so `processing_history`/`get_pipeline_stats()` diverge depending on which surface triggered the run, and no UI client can ever observe an SMS-triggered run either.

### 2.3 Theming / structure

- No `.streamlit/config.toml` exists anywhere in the repo — the app runs on Streamlit's default theme entirely; "bad theme" is literally the unstyled default.
- No design tokens (color palette, spacing, typography scale) exist anywhere; every component (`ui/components/*.py`) hand-rolls its own emoji + `st.success`/`st.error`/`st.warning`/`st.info` calls with inconsistent semantics (e.g. fraud risk `LOW` → green, but a `recommendation` of `"APPROVE"` also → green, using different code paths — `ui/components/status_display.py:23` vs `:43`).
- Layout is a fixed `st.columns([1, 2])` two-pane structure (`ui/main.py:33`) with no responsive/empty/loading states — e.g. `render_progress_tracker` only renders once `processing or completed` is true, so there's a dead middle-of-screen gap on first load.
- `ui/components/report_viewer.py:80` injects a raw base64 PDF `<iframe>` via `unsafe_allow_html=True` — works, but is exactly the kind of ad hoc HTML that should move into a documented component convention rather than be one-off.

### 2.4 Session-state architecture doesn't fit Streamlit's execution model

- Streamlit reruns the entire script top-to-bottom on every interaction; the current code fights this by manually managing 9 separate `st.session_state` keys (`ui/utils/session_state.py`) instead of a single typed state object, making it hard to reason about what triggers a rerun vs. what's stale.

---

## 3. Goals

1. One real-time channel: every claims-processing run (UI-triggered, SMS-triggered, scheduled) broadcasts through the same WebSocket manager, and the Streamlit UI reflects it live, without blocking the UI thread and without fake progress simulation.
2. A real Streamlit theme (`config.toml` + a small design-token layer) applied consistently across every component — one semantic color/status system, not per-component ad hoc choices.
3. A reusable component library (`ui/components/ui/`) — cards, status pills, metric tiles, empty states, skeletons — so pages compose from primitives instead of hand-rolled markdown per screen.
4. Restructured page/information architecture that reflects actual states (idle / running / completed / failed / history) instead of two fixed columns.

## 4. Non-Goals

- No changes to agent business logic, document parsing, or DB models.
- No auth system (assume it stays a trusted internal tool unless a separate task defines otherwise).
- No mobile-responsive design work beyond what Streamlit's layout primitives give for free.
- No migration off Streamlit (§1).

---

## 5. Target Architecture

### 5.1 Real-time channel: consolidate onto FastAPI's native WebSocket support

Retire the standalone `websockets.serve()` process (`websocket_server.py`) and the `RUN_MODE` branch in `main.py`. Replace with a WebSocket route mounted directly on the existing FastAPI app:

```python
# main.py
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_manager.register(websocket)
    try:
        while True:
            await websocket.receive_text()   # UI doesn't need to send anything but must keep the socket alive
    except WebSocketDisconnect:
        await websocket_manager.unregister(websocket)
```

`websocket_manager.py` needs adapting from the raw `websockets` library's `WebSocketServerProtocol` to FastAPI/Starlette's `WebSocket` type (`.send_text()` instead of `.send()`, `WebSocketDisconnect` instead of `websockets.exceptions.ConnectionClosed`). Keep the broadcast/register/unregister API shape — only the transport adapter changes.

Single pipeline instance: every trigger path (UI, `routes/sms.py`, scheduler) must call the **same** `pipeline_singleton.pipeline`, never construct a fresh `ClaimsProcessingPipeline()`. Delete `ui/servicesui/websocket_client.py`'s local instantiation.

UI trigger becomes an HTTP call, not an in-process pipeline call: add a small FastAPI route (e.g. `POST /processing/start`) that calls `pipeline_singleton.pipeline.start_processing(...)` as a background task and returns immediately (mirrors the existing `_process_and_notify` fire-and-forget pattern already used in `routes/sms.py:58`). The Streamlit "Start Processing" button calls this endpoint over plain `requests`/`httpx` and returns instantly — it does not run the pipeline itself.

Streamlit UI becomes a pure WebSocket *subscriber*: a background thread (started once per Streamlit session, via `st.session_state` guarded singleton) holds a persistent `websockets` client connection to `ws://<host>:<port>/ws`, appends every incoming `AgentUpdate` JSON message to a thread-safe queue/list in session state, and the main render loop drains that queue on each rerun. Use `st.fragment(run_every=...)` (Streamlit ≥1.33) or a lightweight `streamlit-autorefresh` component to poll the queue on a short interval (e.g. 500ms–1s) and trigger reruns **only while a run is active** — not a permanent background poll — so idle screens don't churn.

Fix the port mismatch as part of this: since the WS route now lives on the FastAPI app itself, `WEBSOCKET_HOST`/`WEBSOCKET_PORT` env vars become unnecessary — the UI connects to the same host:port as `PORT` (8000). Remove the now-dead vars from `.env`/`.env.example` and document the single port.

### 5.2 Message contract (formalize what already exists)

The `AgentUpdate` shape (`agents/base_agent.py:17`) is already good — just document and freeze it as the contract instead of leaving it implicit:

```json
{
  "agent_id": "claims_agent_ab12cd34" | "claims_agent_ab12cd34_document" | "..._analysis" | "..._report",
  "timestamp": "2026-07-09T12:00:00.000000",
  "status": "initialized" | "processing" | "completed" | "failed" | "paused",
  "stage": "document_processing" | "...",
  "message": "human-readable text",
  "progress": 0.0-100.0,
  "data": { ... } | null,
  "error": "string" | null
}
```

`agent_id` suffixes (`_document`, `_analysis`, `_report`) identify which sub-agent an update belongs to — the UI must demux on this to drive a **4-lane** progress view (master + 3 sub-agents), not the current fabricated 5-stage list in `progress_tracker.py:7`. Real stage taxonomy per agent, taken directly from the code (§ Appendix A), replaces the fake one.

### 5.3 Theming system

- Add `.streamlit/config.toml` defining `[theme]`: primaryColor, backgroundColor, secondaryBackgroundColor, textColor, font. Pick a palette appropriate for an underwriting/claims ops tool (neutral base, one brand accent, restrained use of red/amber/green reserved *only* for risk semantics — not decoration).
- Add a single `ui/theme.py` module exporting design tokens (semantic colors for APPROVE/REJECT/REVIEW, HIGH/MEDIUM/LOW risk, spacing scale) that every component imports instead of hardcoding hex/named colors or picking `st.success`/`st.error` ad hoc. This is what makes "green means approve" and "green means low risk" consistent instead of coincidental.
- One CSS injection point (`ui/theme.py: inject_css()` called once from `ui/main.py`) rather than scattered `unsafe_allow_html` calls per component.

### 5.4 Component library

New `ui/components/ui/` (primitives, no business logic):
- `status_pill(label, tone)` — replaces the repeated `if x == "HIGH": st.error(...) elif ...` blocks in `status_display.py` and `report_viewer.py`.
- `metric_card`, `stat_row` — consistent metric presentation (replaces raw `st.metric` calls with the surrounding card chrome the current design lacks).
- `stage_lane(agent_name, updates)` — renders one sub-agent's live stage list + progress from the real `AgentUpdate` stream.
- `empty_state(message, icon)` — used for the current dead-space gap (§2.3) instead of just not rendering anything.
- `skeleton_block()` — shown while waiting for the first WS message after a run starts, instead of a jump-cut.

Existing files in `ui/components/*.py` (`header.py`, `status_display.py`, `progress_tracker.py`, `report_viewer.py`) get rewritten to *compose* the above primitives rather than hand-roll markup each.

### 5.5 Page / information architecture

Replace the fixed two-column layout with explicit state-driven views sharing one page shell:
- **Idle** — start control + last-run summary (pulled from `pipeline.get_pipeline_stats()`, which currently exists but nothing in the UI surfaces it — `pipeline_controller.py:109`).
- **Running** — live 4-lane stage tracker driven by real WS events (§5.2), cancel control wired to the existing `stop_agent`/`get_active_agents` pipeline methods (already implemented backend-side, currently unused by the UI at all).
- **Completed** — existing `report_viewer.py` tabs, restyled with the component library.
- **Failed** — currently has no distinct treatment at all (`status_display.py` has no `elif` branch for a failed/error state beyond generic `st.error`) — add one, including the `error` field from the WS contract.
- **History** — new, backed by `pipeline.get_processing_history()` (implemented, unused by UI) — a run-log table so both SMS- and UI-triggered runs are visible in one place, closing the "which surface triggered this" gap from §2.2.

---

## 6. Phased Plan

Work top-to-bottom; each phase should be independently shippable/testable.

**Phase 0 — Contract freeze**
Document the `AgentUpdate` schema and full stage taxonomy (Appendix A) as the frozen real-time contract. No code changes; prevents the UI rebuild and the WS consolidation from drifting apart.

**Phase 1 — Backend consolidation (prerequisite for everything else)**
- Mount `/ws` on the FastAPI app; adapt `websocket_manager.py` to Starlette's `WebSocket` type.
- Retire `websocket_server.py` and the `RUN_MODE` branch in `main.py`.
- Add `POST /processing/start` (and `GET /processing/status`, `GET /processing/history` if not already trivially reachable) as thin routes over `pipeline_singleton.pipeline`.
- Delete `ui/servicesui/websocket_client.py`'s local pipeline instantiation.
- Fix/remove the `WEBSOCKET_HOST`/`WEBSOCKET_PORT` env inconsistency.
- **Verify**: trigger a run via `curl -X POST /processing/start`, confirm broadcast messages arrive on a raw `websocat`/`wscat` connection to `/ws` in the correct order with the expected stage names.

**Phase 2 — Theme foundation**
- `.streamlit/config.toml` + `ui/theme.py` design tokens + `inject_css()`.
- No component rewrites yet — apply only to verify the palette/typography looks right in isolation before every component depends on it.

**Phase 3 — Component library**
- Build `ui/components/ui/*` primitives (§5.4) against static/mock data first (no live WS dependency yet), so they're independently reviewable.

**Phase 4 — Live data wiring**
- Background WS-subscriber thread + session-state queue (§5.1).
- Rewire `ui/main.py` start button to call `POST /processing/start` and stop blocking.
- Replace `simulate_progress()` entirely — delete it.
- Wire the 4-lane stage tracker to the real `agent_id`-demuxed stream.

**Phase 5 — Page rebuild**
- Implement the state-driven views from §5.5 using Phase 3 components + Phase 4 data.
- Add the History view (previously nonexistent).
- Add the Failed-state view (previously nonexistent).

**Phase 6 — Cleanup**
- Remove dead code: `websocket_server.py`, unused `RUN_MODE` logic, stale `WEBSOCKET_*` env vars, `ui/utils/session_state.py` keys no longer used once state is consolidated.
- Update `.env.example` to match reality.

---

## 7. File-by-File Change Map

| File | Change |
|---|---|
| `main.py` | Add `@app.websocket("/ws")`; add processing trigger routes; remove `RUN_MODE`/standalone branching from the FastAPI process (keep a CLI-only standalone path if still wanted, separate from `run.py`) |
| `websocket_manager.py` | Port from `websockets` protocol type to Starlette `WebSocket` |
| `websocket_server.py` | **Delete** (superseded by native FastAPI route) |
| `pipeline_singleton.py` | Becomes the *only* pipeline instance used by every entrypoint (SMS, UI, scheduler) |
| `ui/servicesui/websocket_client.py` | **Delete**; replace with a thin HTTP client calling the new `/processing/start` route |
| `ui/main.py` | Non-blocking start call; state-driven view routing (§5.5); remove direct two-column layout |
| `ui/utils/session_state.py` | Consolidate into one typed state object; add WS message queue + connection-thread handle |
| `ui/components/progress_tracker.py` | Rewrite: delete `simulate_progress()`; drive from real WS queue, 4-lane per-agent view |
| `ui/components/status_display.py` | Rewrite using `status_pill`/`metric_card`; add failed-state branch |
| `ui/components/report_viewer.py` | Rewrite using component library; keep PDF iframe approach but move into a documented component |
| `ui/components/header.py` | Restyle via theme tokens; status indicator via `status_pill` |
| `ui/components/ui/*.py` (new) | Component primitives (§5.4) |
| `ui/theme.py` (new) | Design tokens + `inject_css()` |
| `.streamlit/config.toml` (new) | Streamlit native theme |
| `.env`, `.env.example` | Remove `WEBSOCKET_HOST`/`WEBSOCKET_PORT`; document `/ws` lives on `PORT` |

---

## 8. Testing & Verification Plan

- **Backend**: manual WS verification per Phase 1 (`websocat`/`wscat` against `/ws` during a real triggered run); confirm SMS-triggered and UI-triggered runs both appear in `get_processing_history()`.
- **Theme**: visual check in both Streamlit's light and dark viewer modes (Streamlit respects OS/browser theme unless `config.toml` pins one — decide explicitly whether to pin or support both, and state it in `config.toml`).
- **Real-time**: start a run from the UI, confirm the 4-lane tracker updates progressively (not jump-to-100%) and matches the timestamps/stages seen on the raw WS connection.
- **Concurrency**: open two browser tabs during one run, confirm both receive identical live updates (proves broadcast, not per-session simulation).
- **Failure path**: force an agent error (e.g. bad `sender_email`) and confirm the new Failed-state view renders the `error` field instead of a generic message.
- **Regression**: confirm `routes/sms.py` flows (`process_now`, `status`) still work unchanged after `pipeline_singleton` consolidation.
- Per repo convention, run `/verify` against the affected flow before considering any phase done — this is a UI/real-time change with an observable runtime surface, not something typecheck alone can confirm.

---

## 9. Risks & Open Questions

- **Streamlit rerun model vs. persistent WS thread**: Streamlit's execution model doesn't natively love long-lived background threads per session; needs care around thread lifecycle (start once, clean up on session end) to avoid leaking connections across reruns. Prototype this specifically in Phase 4 before building the rest of the live UI on top of it.
- **`st.fragment(run_every=...)` availability**: confirm the installed Streamlit version (not pinned anywhere currently — `ui/requirements_ui.txt` only specifies `>=1.28.0`) supports fragments; pin an exact version as part of Phase 2 if not already resolved.
- **Standalone/CLI run mode**: deciding whether a non-UI, non-SMS "just run it from the CLI" mode is still needed (currently the only consumer of `RUN_MODE=standalone`) — if yes, keep it as a separate thin script rather than branching inside the FastAPI process.
- **Theme pinned vs. adaptive**: needs a decision — pin one theme (simpler, consistent for an internal tool) or support light/dark via Streamlit's automatic OS-theme detection (more polish, more testing surface).

---

## Appendix A — Real Stage Taxonomy (from current code, becomes the frozen contract)

**Master (`agents/master_agent.py`)**: `initialization`(2%) → `document_processing`(5%) → `claims_analysis`(35%) → `report_generation`(70%) → `finalization`(95%) → `completion`(100%); also `error`, `stopping`.

**Document sub-agent (`agents/document_agent.py`)**: `initialization`(5%) → `email_connection`(10%) → `attachment_download`(20%) → `document_preprocessing`(35%) → `email_analysis`(45%) → `document_processing`(60%) → `data_validation`(80%) → `completion`(100%); also `error`.

**Analysis sub-agent (`agents/analysis_agent.py`)**: `initialization`(5%) → `document_query`(15%) → `fraud_detection`(25%) → `exclusion_check`(35%) → `amount_reconciliation`(45%) → `date_validation`(55%) → `duplicate_check`(65%) → `compliance_validation`(75%) → `final_assessment`(85%) → `completion`(100%); also `error`.

**Report sub-agent (`agents/report_agent.py`)**: `initialization`(5%) → `template_preparation`(15%) → `data_compilation`(25%) → `html_generation`(45%) → `pdf_conversion`(65%) → `summary_generation`(80%) → `completion`(100%); also `error`.
