# 05 — Phased Build Order, Testing, Deployment & Cutover

Status: **Planning — implementation not yet started.**
Depends on: [01](./01-architecture-decision.md)-[04](./04-component-page-implementation.md).

---

## 1. Phased build order

Each phase independently shippable/testable, same discipline the prior
Streamlit plan used.

**Phase 0 — Backend additions** ([02](./02-backend-api-contract.md))
- Add CORS middleware, `FRONTEND_ORIGINS` env var.
- Add `GET /processing/result/{agent_id}/report.pdf`.
- **Verify**: `curl` the new PDF route against a completed run's
  `agent_id`; confirm `content-type: application/pdf` and a valid file.
  Confirm a cross-origin `fetch` from a throwaway `http://localhost:5173`
  page succeeds against `/processing/status`.

**Phase 1 — Frontend scaffold** ([03](./03-frontend-project-setup.md))
- Vite scaffold, Tailwind + shadcn init, folder structure, theme tokens.
- API client, WS hook, run store, stage taxonomy — no UI yet.
- **Verify**: a throwaway test page shows live WS connection state flipping
  to `open` against a running `uvicorn main:app`.

**Phase 2 — Component library** ([04](./04-component-page-implementation.md) §1-2)
- Build every component against static/mock `AgentUpdate`/`MasterResult`
  fixtures, no live data. Storybook is optional here — a simple
  `/dev-fixtures` route rendering each component with mock props is enough
  given the small component count; don't add Storybook tooling for ~12
  components.
- **Verify**: visually review each component in isolation (light theme only,
  per [01](./01-architecture-decision.md) §5) before wiring real data.

**Phase 3 — Live wiring** ([04](./04-component-page-implementation.md) §3-4)
- Wire `Dashboard`, `Sidebar`, `ProgressTracker`, `StatusDisplay` to the real
  store/WS/API.
- **Verify**: start a run from the UI, confirm the 4-lane tracker updates
  progressively (not jump-to-100%) matching timestamps seen on a parallel
  `python test_websocket_connection.py` session.

**Phase 4 — Report & History pages**
- `ReportViewer`, `CompletedView`, `History` page.
- **Verify**: completed run shows PDF inline + downloadable; History page
  shows both a UI-triggered run and (trigger one via `curl -X POST
  /sms/incoming` with a `process_now` body, or directly via
  `pipeline_singleton`) an SMS-triggered run in the same table.

**Phase 5 — Failed-state & edge cases**
- Failed-state panel (`StatusDisplay` §04 §2), single-active-run rejection
  toast (`Sidebar` §04 §3), reconnect banner (`Header`).
- **Verify**: force a failure (e.g. temporarily point `CLAIMS_SENDER_EMAIL`
  at an address with no matching email) and confirm the failed panel renders
  `error` instead of hanging on "running."

**Phase 6 — Build & deploy** (§3 below)

---

## 2. Testing strategy

- **Unit (Vitest + React Testing Library)**: `runStore` reducer logic
  (`applyUpdate`, `view()`) is the highest-value target — it's the ported
  state machine from §03 §7 and deserves the same rigor the original
  `RunState` logic implied it needed (new-run detection, stale-broadcast
  rejection, terminal states). Test each branch with fixture `AgentUpdate`
  sequences. Also unit-test `StatusPill`/`StageLane` render correctly per
  tone/status prop.
- **Integration**: mock the WS server (`vitest-websocket-mock` or a small
  hand-rolled `ws` test server) to drive a fake run through
  initialization → completion and assert the Dashboard transitions through
  idle → running → completed without hitting a real backend.
- **E2E (Playwright)**, against a real `uvicorn main:app` + real agents (or a
  test double sender email with fixture emails, if agent execution is too
  slow/costly to run in CI): start a run from the browser, assert the
  4-lane tracker reaches 100%, assert the PDF iframe loads, assert History
  shows the run. This is the one layer that actually proves the
  frontend-to-backend wiring works, not just the frontend's internal logic.
- **Manual regression checklist** (run before considering the migration
  done, same checks the Streamlit plan specified — they're transport-
  agnostic):
  - Two browser tabs open during one run see identical live updates
    (proves broadcast fan-out, not per-client simulation).
  - `routes/sms.py` flows (`process_now`, `status`, `schedule`) still work
    unchanged — confirm via a real or sandbox Africa's Talking webhook call.
  - Scheduler-triggered runs (`services/scheduler_service.py`) show up in
    the React History page identically to UI-triggered ones.
  - Force-killing the FastAPI process mid-run and restarting it: frontend
    should show a reconnecting state, then resume receiving broadcasts once
    the server is back (a *new* run, since in-memory `pipeline_singleton`
    state doesn't survive a restart — same limitation as before, not a
    regression to fix here).

---

## 3. Build & deployment

Recommended: **single-origin production deploy** — FastAPI serves the built
SPA directly, eliminating CORS/multi-origin concerns in prod entirely (CORS,
§02 §2.1, only matters for local dev where Vite's dev server and `uvicorn`
run as separate processes on separate ports).

```python
# main.py — added once frontend/dist exists
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def spa_catch_all(full_path: str):
    # Any path not matched by an API route above falls through to this —
    # React Router handles client-side routing from here.
    return FileResponse("frontend/dist/index.html")
```

Order matters: this catch-all route must be registered **after**
`sms_router`/`processing_router`/`/ws`, so API routes still take priority.

Build/run sequence for a deploy:
```bash
cd frontend && npm run build   # produces frontend/dist/
cd .. && uvicorn main:app --host 0.0.0.0 --port 8000
```

Alternative (not recommended as the default, but a reasonable fallback if
the frontend ever needs independent deploy cadence/CDN hosting): deploy
`frontend/dist` to a static host (Netlify/Vercel/S3+CloudFront) and keep
`FRONTEND_ORIGINS` pointed at that origin. Revisit only if a concrete need
for independent frontend deploys shows up — don't split the deploy
preemptively.

---

## 4. Cutover checklist

- [x] Streamlit UI deleted (`ui/`, `run_ui.py`, `.streamlit/`) — done as part
      of this migration's first step, before any of these docs were written.
- [ ] Phase 0 backend additions merged and verified.
- [ ] Phases 1-5 frontend work merged and verified per-phase.
- [ ] `frontend/README.md` (or a section in the repo's own README, if one is
      added later) documents `npm install && npm run dev` for local dev,
      alongside the existing `uvicorn main:app` instructions.
- [ ] `.env.example` updated with `FRONTEND_ORIGINS` (§02 §2.3).
- [ ] Manual regression checklist (§2) run once against the finished
      frontend, not just per-phase smoke checks.
- [ ] Confirm no remaining references to `streamlit`, `run_ui.py`, or
      `.streamlit/` anywhere in the repo (`grep -ri streamlit .` should
      return nothing outside these `docs/*.md` files, which document the
      migration and are expected to mention it historically).
