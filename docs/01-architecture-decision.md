# 01 — React Migration: Decision Record & Target Architecture

Status: **Planning — implementation not yet started.**
Supersedes: the root `WORKFLOW.md` that previously existed in this repo, which
recorded a decision to *stay* on Streamlit. That decision is reversed by this
document. The Streamlit UI (`ui/`, `run_ui.py`, `.streamlit/`) has already
been deleted from the repository as part of this migration.

Scope: frontend only. `agents/*`, `document_processing/*`, `services/*`,
`models/*`, DB schema, and the SMS/scheduler flows are out of scope and must
keep working unchanged throughout.

---

## 1. Decision

**Migrate the UI from Streamlit to a standalone React single-page app**,
talking to the existing FastAPI backend over REST + a native WebSocket
connection.

### Why this is a small, low-risk migration

The backend work a Streamlit-to-React migration normally requires —
consolidating onto one real-time channel, one pipeline instance, and a
documented event contract — **is already done**. Reading the current code:

- `main.py:32` mounts `@app.websocket("/ws")` directly on the FastAPI app
  used in production (`run.py` → `uvicorn main:app`).
- `websocket_manager.py` is already a Starlette-native broadcast manager
  (`register`/`unregister`/`broadcast` over `starlette.websockets.WebSocket`).
- `pipeline_singleton.py` is the **one** `ClaimsProcessingPipeline` instance,
  wired with the real `websocket_manager`, and used by every trigger path:
  `routes/sms.py`, `services/scheduler_service.py`, and (formerly) the
  Streamlit UI via HTTP.
- `routes/processing.py` already exposes a full REST surface over that
  singleton: `POST /processing/start`, `GET /processing/status`,
  `GET /processing/history`, `GET /processing/result/{agent_id}`,
  `POST /processing/stop/{agent_id}`.
- Every agent (`agents/master_agent.py`, `document_agent.py`,
  `analysis_agent.py`, `report_agent.py`) already emits a structured
  `AgentUpdate` JSON event via `self.send_update(...)`
  (`agents/base_agent.py:38`) broadcast to *every* connected client.

In other words: this is not "rebuild the real-time backend, then bolt on
React." It's "point a new frontend at a real-time API that already exists,"
plus a small number of backend additions React specifically needs that
Streamlit didn't (CORS, binary file serving for PDFs — see
[02-backend-api-contract.md](./02-backend-api-contract.md)).

### Why leave Streamlit at all, then?

Streamlit was capped on exactly the things this tool increasingly needs:
custom layout control, componentized UI reuse across screens, a real
client-side routing/state model instead of full-script reruns, and a
deployable, brandable frontend independent of the Python process's request
lifecycle. React removes all four ceilings at the cost of a build pipeline —
acceptable for a tool that's clearly graduating past "internal script with a
UI bolted on."

---

## 2. Non-Goals

- No changes to agent business logic, document parsing, or DB models.
- No new auth system in this phase — this stays a trusted internal tool.
  CORS is scoped to known frontend origins (dev + prod), not public access.
  Revisit if the tool is ever exposed outside a trusted network.
- No mobile-native app — a responsive web SPA is sufficient.
- No change to the SMS-triggered or scheduler-triggered flows
  (`routes/sms.py`, `services/scheduler_service.py`) beyond what's already
  true today: they go through `pipeline_singleton`, same as the new UI.

---

## 3. Target Architecture

```
                         ┌─────────────────────────────┐
                         │      FastAPI (main.py)       │
                         │                               │
  Browser  ── HTTPS ───▶ │  REST: /processing/*         │
  (React SPA)             │  WS:   /ws                   │
                         │                               │
                         │  pipeline_singleton.pipeline  │──▶ agents/* (unchanged)
                         │  websocket_manager (broadcast)│
                         └─────────────────────────────┘
                                    ▲
                    routes/sms.py ──┘   services/scheduler_service.py ──┘
                    (unchanged, same pipeline instance)
```

- **Dev**: Vite dev server (`localhost:5173`) proxies/CORS-calls the FastAPI
  process (`localhost:8000`). Two processes, two terminals — same pattern as
  Streamlit's `run.py` + `run_ui.py` had, just a different frontend process.
- **Prod**: `vite build` output is served as static files directly by the
  FastAPI app (single origin, no CORS needed in prod). See
  [05-testing-deployment-cutover.md](./05-testing-deployment-cutover.md) §Deployment
  for the exact wiring.
- **Real-time**: the SPA opens one WebSocket connection to `/ws` for the
  lifetime of the app (not per-page), receives `AgentUpdate` broadcasts, and
  demuxes them into per-agent "lanes" client-side — the same demuxing logic
  the deleted Streamlit UI used (`lane_for_agent_id`/`root_agent_id`), now
  ported to TypeScript (see [03](./03-frontend-project-setup.md) and
  [04](./04-component-page-implementation.md)).
- **Multiple clients**: `websocket_manager.broadcast()` already fans out to
  every connected socket — two browser tabs, or a browser tab + a raw
  `wscat` session, all see identical live updates. No per-client fan-out
  logic needed anywhere.

---

## 4. Technology Choices

| Concern | Choice | Why |
|---|---|---|
| Build tool | **Vite** | Fast dev server, first-class React+TS template, trivial static build output for FastAPI to serve. |
| Framework | **React 18 + TypeScript** | Team already reads Python type hints; TS keeps the `AgentUpdate` contract enforced at compile time on the frontend too. |
| Routing | **React Router v6** | Two real routes to start (`/`, `/history`); still worth a router over conditional rendering so URLs are shareable/bookmarkable and back/forward works. |
| Server-state (REST) | **TanStack Query** | `GET /processing/status`, `/history`, `/result/{id}` are cache-and-refetch-shaped problems (matches what `st.cache`/manual refetch was doing ad hoc in Streamlit) — TanStack Query gives polling, retry, and cache invalidation for free. |
| Client-state (live run) | **Zustand** | The WS-derived "what screen are we on" state (`RunState` in the deleted `ui/utils/session_state.py`) is a single small store with one reducer-like `applyUpdate` action — Zustand is the least ceremony for that; Redux would be overkill for one store. |
| Styling / components | **Tailwind CSS + shadcn/ui (Radix primitives)** | Radix gives accessible `Tabs`, `Dialog`, `Table` primitives for free (report viewer tabs, history table); Tailwind lets the existing design-token palette (§5) map directly to config instead of hand-rolled CSS-in-JS. |
| WebSocket | **Native browser `WebSocket` API**, wrapped in one custom hook | No abstraction needed beyond reconnect/backoff, which is ~30 lines (ports `ui/servicesui/ws_subscriber.py`'s reconnect loop directly). |
| PDF viewing | **`<iframe>` / `<embed>` against a direct PDF URL** | Browsers render PDFs natively; no client-side PDF.js dependency needed as long as the backend serves the file with the right content type (§02). |
| Dates | **date-fns** | Formatting `AgentUpdate.timestamp` / history table timestamps. |

---

## 5. Theming

Carry forward the same design-token system the Streamlit UI already
converged on (`ui/theme.py`, now deleted but the values are sound and
domain-appropriate) — don't redesign the palette, port it:

- **Base**: neutral background (`#FFFFFF` / `#F4F6F7`), text `#1A2226`.
- **Brand accent**: `#1D4E5F` (a desaturated teal — reads as "ops tool," not
  "consumer app").
- **Semantic risk colors** — the important invariant to preserve: **the same
  three tones drive both `overall_recommendation` (APPROVE/REVIEW/REJECT)
  and `fraud_risk_level` (LOW/MEDIUM/HIGH)**, so green always means "good
  outcome" regardless of which field it's labeling:
  - success (`APPROVE` / `LOW`): fg `#0F5132`, bg `#E8F5EE`, border `#A8D5BC`
  - warning (`REVIEW` / `MEDIUM`): fg `#7A5A00`, bg `#FFF6DE`, border `#E8D48A`
  - danger (`REJECT` / `HIGH`): fg `#7A1F1F`, bg `#FBEAEA`, border `#E8B4B4`
  - info / neutral: as used for agent status pills (`processing`, `idle`, etc.)
- **Theme mode**: pinned light theme for v1, same call the Streamlit plan
  made — this is a small set of known internal users (desk/ops room), and a
  single consistent look reduces support burden more than dark-mode polish is
  worth right now. Unlike Streamlit's `config.toml`, Tailwind makes adding a
  `dark:` variant later a config change, not a rewrite — revisit only if
  asked for.

Exact token → Tailwind config mapping is in
[03-frontend-project-setup.md](./03-frontend-project-setup.md) §Theme setup.

---

## 6. Information Architecture

Two routes, replacing the Streamlit sidebar-radio + conditional views:

- **`/` — Dashboard**: state-driven view (idle / running / completed /
  failed), matching the Streamlit `RunState.view` state machine exactly —
  see [04](./04-component-page-implementation.md) for the ported logic.
- **`/history`** — run-log table backed by `GET /processing/history` +
  `GET /processing/status`, identical data source to the deleted
  `ui/components/history_view.py`, now a React page.

A persistent header shows live WS connection status (connected/reconnecting)
— something the Streamlit UI never surfaced explicitly.

---

## 7. Document Map

| Doc | Covers |
|---|---|
| 01 (this file) | Decision, target architecture, tech stack, theme direction |
| [02-backend-api-contract.md](./02-backend-api-contract.md) | Frozen REST + WS contract; backend additions React needs (CORS, PDF serving) |
| [03-frontend-project-setup.md](./03-frontend-project-setup.md) | Scaffold, folder structure, API client, WS hook, store, routing, Tailwind theme setup |
| [04-component-page-implementation.md](./04-component-page-implementation.md) | Component inventory, page specs, ported state-machine logic |
| [05-testing-deployment-cutover.md](./05-testing-deployment-cutover.md) | Phased build order, testing strategy, build/deploy, cutover checklist |

---

## 8. Risks & Open Questions

- **CORS scope in prod**: if the SPA is ever served from a different origin
  than the API in production, `FRONTEND_ORIGIN` (§02) must be set precisely —
  don't default to `*` once real user data is flowing over these endpoints.
- **Single active run constraint**: `routes/processing.py:20` already
  rejects a second `/start` while one agent is active — the frontend must
  surface this rejection clearly (§04 Sidebar/Controls spec) rather than
  silently failing the button click.
- **PDF serving approach**: static-mount vs. dedicated route — decided in
  §02 (dedicated route, not a raw static mount) to avoid exposing the
  `reports/` directory's raw filesystem structure.
- **Long-lived WS reconnect UX**: decide, when building §04's connection
  indicator, whether a dropped connection during an active run should show a
  blocking error or a soft "reconnecting…" banner that keeps the last-known
  state visible. Recommend the latter — the backend keeps processing
  regardless of any given client's connection state.
