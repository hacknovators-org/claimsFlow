# 02 — Backend API Contract & Required Backend Changes

Status: **Planning — implementation not yet started.**
Scope: `main.py`, `routes/processing.py`, `websocket_manager.py`,
`pipeline_controller.py`, `pipeline_singleton.py`, `.env`/`.env.example`.
Out of scope: agent logic, DB models — this document only *documents* the
existing contract and specifies the *few* additions the React frontend needs
that Streamlit didn't.

---

## 1. What already exists (frozen contract, do not redesign)

All of the below is implemented and working today. This section documents it
as the contract the React frontend is built against — treat any change to
these shapes as a breaking change requiring a version bump in this doc.

### 1.1 REST endpoints (`routes/processing.py`, prefix `/processing`)

| Method | Path | Request | Response | Notes |
|---|---|---|---|---|
| `POST` | `/processing/start` | query param `sender_email` (optional, defaults to `CLAIMS_SENDER_EMAIL` env var) | `{"started": true, "sender_email": str}` or `{"started": false, "reason": str}` | Fire-and-forget: returns immediately, run progresses via `/ws`. Rejects if `pipeline.get_active_agents()` is non-empty — **only one run can be active pipeline-wide at a time.** |
| `GET` | `/processing/status` | — | `PipelineStats` (§1.3) | Snapshot of aggregate stats + last run. |
| `GET` | `/processing/history` | query param `limit` (default 50) | `{"history": ProcessingRecord[]}` (§1.4) | Both UI- and SMS-triggered runs appear here, since both go through `pipeline_singleton`. |
| `GET` | `/processing/result/{agent_id}` | path param `agent_id` (the **master** agent's id) | Full result object (§1.5), or `404` if not yet available | This is the master agent's `_finalize_results()` output — includes `report_generated.pdf_path`, which is a **server-local filesystem path**, not fetchable directly by a browser (see §2.2). |
| `POST` | `/processing/stop/{agent_id}` | path param `agent_id` | `{"stopped": bool}` | Calls `pipeline.stop_agent()`; only works while that agent is active. |

### 1.2 WebSocket (`main.py:32`)

`ws://<host>:<port>/ws` — one shared broadcast channel, no per-client
filtering. Client sends nothing (server just keeps the socket alive reading
`receive_text()` until disconnect). Every connected client gets every
`AgentUpdate` from every active run.

### 1.3 `PipelineStats` shape (`pipeline_controller.py:114`)

```ts
interface PipelineStats {
  total_processed: number;
  successful: number;
  failed: number;
  success_rate: number;          // 0-100
  active_agents: number;
  average_processing_time: number; // seconds
  recommendations_breakdown: Record<string, number>; // e.g. {"APPROVE": 3, "REVIEW": 1}
  last_processing: ProcessingRecord | null;
}
```

### 1.4 `ProcessingRecord` shape (`pipeline_controller.py:37`, `:72`)

```ts
interface ProcessingRecord {
  agent_id: string;
  sender_email: string;
  start_time: string;   // ISO 8601
  end_time: string;      // ISO 8601
  duration_seconds?: number; // absent on FAILED records built before start_time was known
  status: "COMPLETED" | "FAILED";
  recommendation?: string;         // "APPROVE" | "REJECT" | "REVIEW" — COMPLETED only
  critical_issues_count?: number;  // COMPLETED only
  report_path?: string;            // COMPLETED only, server-local path
  error?: string;                  // FAILED only
}
```

### 1.5 `/processing/result/{agent_id}` shape (`agents/master_agent.py:77` `_finalize_results`)

```ts
interface MasterResult {
  master_agent_id: string;
  processing_status: "COMPLETED";
  overall_recommendation: "APPROVE" | "REJECT" | "REVIEW";
  fraud_risk_level: "LOW" | "MEDIUM" | "HIGH" | "UNKNOWN";
  document_processing: {
    status: string;
    files_processed: number;
    email_completeness: string;
    missing_documents: string[];
  };
  analysis_summary: {
    fraud_analysis_completed: boolean;
    exclusion_check_completed: boolean;
    reconciliation_completed: boolean;
    date_validation_completed: boolean;
    duplicate_check_completed: boolean;
    compliance_validation_completed: boolean;
  };
  critical_issues: string[];
  report_generated: {
    pdf_path: string | null;       // server-local path, e.g. "reports/claims_analysis_report_20260709_120000.pdf"
    generation_timestamp: string;  // ISO 8601
    executive_summary: string;
  };
  next_steps: string[];
  processing_metadata: {
    email_sender: string;
    email_subject: string;
    total_processing_agents: number;
    agent_statuses: Record<string, string>; // {"document": "completed", "analysis": "completed", "report": "completed"}
  };
}
```

Note: `report_generated.html_content` (the full rendered HTML report,
`agents/report_agent.py:41`) is present on the **agent's own** `self.results`
but is **not** currently included in the trimmed `report_generated` block
that `master_agent._finalize_results` builds (`agents/master_agent.py:98`
only pulls `pdf_path`, `generation_timestamp`, `executive_summary`). If the
React "Full Report" tab needs the raw HTML (the deleted Streamlit
`report_viewer.py:76` rendered it in an expander), either:
  (a) add `"html_content": report_results.get("html_content")` to that dict
      in `_finalize_results`, or
  (b) skip it — the PDF (§2.2) already contains the same content, and one
      canonical rendering (PDF) is simpler than maintaining two.
  Recommend **(b)** unless a concrete need for inline HTML surfaces later —
  don't add the field speculatively.

### 1.6 `AgentUpdate` WS message shape (`agents/base_agent.py:17`, `:58`)

```ts
interface AgentUpdate {
  agent_id: string;       // "claims_agent_ab12cd34" (master) | "..._document" | "..._analysis" | "..._report"
  timestamp: string;      // ISO 8601
  status: "initialized" | "processing" | "completed" | "failed" | "paused";
  stage: string;          // see stage taxonomy below
  message: string;        // human-readable
  progress: number;       // 0.0-100.0
  data: Record<string, unknown> | null;
  error: string | null;
}
```

`agent_id` suffix (`_document` / `_analysis` / `_report`, none = master)
identifies which of the 4 lanes an update belongs to. Port this demuxing
logic to TypeScript exactly as the deleted `ui/utils/stage_taxonomy.py` had
it — see [03-frontend-project-setup.md](./03-frontend-project-setup.md) for
the ported module.

### 1.7 Stage taxonomy (frozen — mirror of the agent code, not aspirational)

**Master** (`agents/master_agent.py`): `initialization`(2%) →
`document_processing`(5%) → `claims_analysis`(35%) →
`report_generation`(70%) → `finalization`(95%) → `completion`(100%); also
`error`, `stopping`.

**Document** (`agents/document_agent.py`): `initialization`(5%) →
`email_connection`(10%) → `attachment_download`(20%) →
`document_preprocessing`(35%) → `email_analysis`(45%) →
`document_processing`(60%) → `data_validation`(80%) → `completion`(100%);
also `error`.

**Analysis** (`agents/analysis_agent.py`): `initialization`(5%) →
`document_query`(15%) → `fraud_detection`(25%) → `exclusion_check`(35%) →
`amount_reconciliation`(45%) → `date_validation`(55%) →
`duplicate_check`(65%) → `compliance_validation`(75%) →
`final_assessment`(85%) → `completion`(100%); also `error`.

**Report** (`agents/report_agent.py`): `initialization`(5%) →
`template_preparation`(15%) → `data_compilation`(25%) →
`html_generation`(45%) → `pdf_conversion`(65%) → `summary_generation`(80%) →
`completion`(100%); also `error`.

---

## 2. Required backend changes

Everything above already works. These are the only backend changes this
migration needs.

### 2.1 CORS middleware (`main.py`)

The React dev server runs on a different origin (`http://localhost:5173`)
than the API (`http://localhost:8000`). Add:

```python
from fastapi.middleware.cors import CORSMiddleware

FRONTEND_ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

Add `FRONTEND_ORIGINS=http://localhost:5173` to `.env.example`. In
production, if the SPA is served from the same FastAPI process (recommended,
see [05](./05-testing-deployment-cutover.md) §Deployment), CORS becomes a
no-op there — same origin, no preflight needed — but keep the middleware
configurable rather than hardcoding dev-only origins, since a split
frontend/backend deploy is a reasonable fallback.

Starlette's `WebSocketRoute` doesn't enforce CORS the same way HTTP routes do
(browsers don't send `Origin` preflight for WS the way they do for
`fetch`/`XHR`), so no separate WS-specific CORS change is needed — confirm
this holds when implementing by testing a cross-origin WS connection from
the Vite dev server.

### 2.2 PDF report serving endpoint

`report_generated.pdf_path` (§1.5) is a path on the **server's** filesystem
(`reports/claims_analysis_report_<timestamp>.pdf`, written by
`agents/report_agent.py:512` `_generate_pdf_report`). The deleted Streamlit
UI could `open(pdf_path, "rb")` directly because it ran in the same process;
a browser cannot. Add a dedicated route rather than a raw
`StaticFiles(directory="reports")` mount, so the frontend never needs to
know the raw filename/path — it only needs the `agent_id` it already has:

```python
# routes/processing.py
from fastapi.responses import FileResponse

@router.get("/result/{agent_id}/report.pdf")
async def get_report_pdf(agent_id: str):
    result = pipeline.get_result(agent_id)
    if result is None:
        raise HTTPException(status_code=404, detail="No result for this agent_id yet")
    pdf_path = result.get("report_generated", {}).get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="No PDF report generated for this run")
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))
```

Why a dedicated route over a static mount:
- No directory listing / path traversal surface — the only input is
  `agent_id`, which is looked up server-side against `results_by_agent`
  (`pipeline_controller.py:15`), never used to build a filesystem path
  directly from client input.
- The frontend's PDF `<iframe src="...">` / download link is stable
  (`/processing/result/{agent_id}/report.pdf`) even if the on-disk naming
  scheme in `report_agent.py` changes later.
- Matches the existing convention of exposing agent data by `agent_id`, not
  by raw path (`GET /processing/result/{agent_id}` already does this).

### 2.3 Env vars

Add to `.env.example`:

```
# React frontend origin(s) allowed to call this API in dev (comma-separated).
# Not needed in prod if the SPA is served from this same FastAPI process.
FRONTEND_ORIGINS=http://localhost:5173
```

No other env changes needed — `PORT`/`HOST` already correctly serve both
REST and WS from one process (this was already fixed in the prior Streamlit
iteration; there is no `WEBSOCKET_PORT`/`WEBSOCKET_HOST` to clean up).

### 2.4 Optional: serve the built SPA from FastAPI (production only)

Deferred to [05-testing-deployment-cutover.md](./05-testing-deployment-cutover.md)
§Deployment — it's a `StaticFiles` mount + catch-all route added to
`main.py`, done once the frontend actually has a build to serve. Don't add
this scaffolding before there's a `dist/` to point it at.

---

## 3. Verification

Before building any frontend code against this contract, verify it
end-to-end exactly as the prior Streamlit-era plan did (this still works
today and is a useful sanity check before layering React on top):

```bash
# Terminal 1
uvicorn main:app --reload

# Terminal 2 — watch broadcasts
python test_websocket_connection.py

# Terminal 3 — trigger a run
curl -X POST "http://localhost:8000/processing/start"
```

Confirm: `AgentUpdate` messages arrive on the WS connection in stage order
matching §1.7, `GET /processing/status` reflects the run once complete, and
(once §2.2 is implemented) `GET /processing/result/{agent_id}/report.pdf`
returns a valid PDF with `content-type: application/pdf`.
