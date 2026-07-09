# 🛡️ Hacknovators — AI Insurance Claims Processing System

An intelligent, fully automated pipeline that reads reinsurance **cash call emails**, validates the attached documents against treaty rules, detects fraud, and generates a compliance PDF report — all powered by **GPT-4** and **LangChain**.

---

## 📋 Table of Contents

- [Overview](#overview)
- [How It Works — End-to-End Flow](#how-it-works--end-to-end-flow)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Real-Time UI](#real-time-ui)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the System](#running-the-system)
- [Output](#output)

---

## Overview

In the reinsurance industry, cedants (insurance companies) submit **cash calls** — requests for reimbursement — via email with supporting documents (bordereaux, statements, treaty slips, notification letters, etc.).

This system **automates the entire claims auditing workflow**:

1. Fetches emails from a specific cedant via Gmail IMAP
2. Downloads and parses all document attachments
3. Runs multi-layered AI validation (fraud, exclusions, reconciliation, dates, duplicates, compliance)
4. Produces a final **APPROVE / REJECT / REVIEW** recommendation
5. Generates a professionally formatted **PDF report**
6. Streams all progress live to a **Streamlit dashboard** via WebSocket

---

## How It Works — End-to-End Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                          TRIGGER                                 │
│  User clicks "Start Processing" in UI (or runs standalone mode)  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              STAGE 1 — DOCUMENT PROCESSING                       │
│                                                                  │
│  1. Connect to Gmail via IMAP SSL                                │
│  2. Search inbox for emails from the cedant email address        │
│  3. Download all attachments (PDF, Excel, Word, etc.)            │
│  4. Parse each file:                                             │
│       • PDF  → PyMuPDF / pypdf                                   │
│       • DOCX → python-docx                                       │
│       • Other → unstructured                                     │
│  5. Classify documents:                                          │
│       • Bordereaux (claims list)                                 │
│       • Statement of Account                                     │
│       • Treaty / Slip                                            │
│       • Notification Letter                                      │
│       • Supporting Evidence                                      │
│  6. Embed all text into FAISS vector store (OpenAI embeddings)   │
│  7. GPT-4 analyzes email body: completeness + missing docs check │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              STAGE 2 — CLAIMS ANALYSIS                           │
│                                                                  │
│  LangChain ReAct Agent (GPT-4) runs 6 analysis checks:          │
│                                                                  │
│  ① FRAUD DETECTION                                               │
│     Looks for inflated amounts, inconsistent dates, suspicious   │
│     patterns → Returns: LOW / MEDIUM / HIGH risk                 │
│                                                                  │
│  ② TREATY EXCLUSION CHECK                                        │
│     Extracts exclusion clauses and validates each claim          │
│                                                                  │
│  ③ AMOUNT RECONCILIATION                                         │
│     Bordereaux totals vs. Statement of Account totals            │
│                                                                  │
│  ④ DATE VALIDATION                                               │
│     Dates of loss vs. policy period + accounting quarter check   │
│                                                                  │
│  ⑤ DUPLICATE CLAIM DETECTION                                     │
│     Queries PostgreSQL for previously processed matching claims  │
│                                                                  │
│  ⑥ REGULATORY COMPLIANCE                                         │
│     Required fields, reporting deadlines, formatting rules       │
│                                                                  │
│  → Final Assessment: APPROVE / REJECT / REVIEW                  │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│              STAGE 3 — REPORT GENERATION                         │
│                                                                  │
│  1. Collect all analysis results                                 │
│  2. Render Jinja2 HTML report template with findings             │
│  3. Convert HTML → professional PDF via WeasyPrint               │
│  4. Save to /reports directory with timestamp                    │
│  5. Return PDF path for display in the UI                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Component Map

```
hacknovators-main/
│
├── main.py                    ← Core async entry point
├── pipeline_controller.py     ← Manages agent lifecycle
├── websocket_server.py        ← Receives UI commands, sends results
├── websocket_manager.py       ← Broadcasts real-time updates
│
├── agents/
│   ├── base_agent.py          ← Abstract base (status, progress, broadcasting)
│   ├── master_agent.py        ← Orchestrates 3 sub-agents in sequence
│   ├── document_agent.py      ← Gmail + document parsing + FAISS
│   ├── analysis_agent.py      ← LangChain ReAct agent + 6 analysis tools
│   └── report_agent.py        ← Jinja2 + WeasyPrint PDF generation
│
├── services/
│   ├── gmail_reader.py        ← Gmail IMAP connector + attachment downloader
│   ├── agent_tools.py         ← LangChain @tool definitions
│   ├── email_analyzer.py      ← GPT-4 email completeness analysis
│   └── document_processor.py ← File type detection + text extraction routing
│
├── document_processing/
│   ├── pipeline.py            ← Document ingestion and chunking
│   └── processors/
│       └── pdf_processor.py   ← PDF-specific text extraction (PyMuPDF)
│
├── models/
│   └── cash_call.py           ← SQLAlchemy ORM model for processed claims
│
├── database.py                ← SQLAlchemy engine + session setup
│
├── ui/
│   ├── main.py                ← Streamlit dashboard
│   ├── components/            ← Header, progress tracker, report viewer
│   ├── servicesui/            ← WebSocket client for UI ↔ backend
│   └── utils/                 ← Session state management
│
├── reports/                   ← Generated PDF reports (output)
├── run.py                     ← Starts FastAPI backend
├── run_ui.py                  ← Starts Streamlit UI
└── run_enhanced_system.py     ← Starts WebSocket server + UI together
```

### Communication Flow

```
Streamlit UI
    │  WebSocket ws://localhost:8765
    │  ← { type: "start_processing", sender_email: "..." }
    │  → progress updates, tool events, final results
    ▼
WebSocketServer
    ▼
ClaimsProcessingPipeline
    ▼
MasterClaimsAgent
    ├── DocumentAgent ──────── Gmail → Files → FAISS
    ├── ClaimsAnalysisAgent ── FAISS + LangChain → Analysis
    └── ReportGenerationAgent ─ Results → Jinja2 → PDF
```

---

## Agent Pipeline

### Stage 1 — Document Agent
**File:** `agents/document_agent.py`

| Step | Action |
|------|--------|
| 1 | Connect to Gmail via IMAP4 SSL |
| 2 | Search for emails from the target sender |
| 3 | Download attachments to `downloads/` |
| 4 | Extract text (PyMuPDF / python-docx / unstructured) |
| 5 | Classify each document by type |
| 6 | Build FAISS vector index from all text chunks |
| 7 | GPT-4 checks email for missing required documents |

**Output:** FAISS vector store path + email completeness analysis

---

### Stage 2 — Claims Analysis Agent
**File:** `agents/analysis_agent.py`

Uses a **LangChain ReAct Agent** that reasons step-by-step and picks the right tool for each check.

**LangChain Tools** (`services/agent_tools.py`):

| Tool | Purpose |
|------|---------|
| `query_documents` | Semantic search over FAISS vector store |
| `extract_bordereaux_claims` | Pulls structured claims table data |
| `extract_treaty_exclusions` | Extracts exclusion clauses from treaty docs |
| `validate_claim_against_exclusions` | Cross-checks claims vs. exclusions |
| `extract_statement_totals` | Gets financial totals from statement docs |
| `compare_bordereaux_vs_statement` | Reconciles amounts between documents |
| `validate_claim_dates` | Checks date of loss vs. policy period |
| `check_duplicate_claims_in_database` | SQL query against historical claims DB |
| `extract_notification_details` | Parses claim notification letters |
| `validate_accounting_quarter` | Confirms correct quarter is being billed |
| `calculate_recovery_amounts` | Computes treaty recovery amounts |

**Output:** Full analysis results + `APPROVE / REJECT / REVIEW` recommendation

---

### Stage 3 — Report Generation Agent
**File:** `agents/report_agent.py`

Converts all analysis results into a PDF report via Jinja2 templating + WeasyPrint.

---

## Real-Time UI

**File:** `ui/main.py` — built with Streamlit

| Tab | Content |
|-----|---------|
| 🔄 Live Progress | Stage progress bar, active tool being executed |
| 📈 Analytics | Stage duration chart, timing breakdown |
| 📊 Results | Final recommendation, critical issues, PDF viewer |

Sidebar: control panel (start/stop), agent status, quick stats.

---

## Tech Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| LLM | OpenAI GPT-4 | Claims analysis + email understanding |
| Agent Framework | LangChain ReAct | Tool-using reasoning loop |
| Vector Search | FAISS + OpenAI Embeddings | Semantic document retrieval |
| Email | imaplib (Gmail IMAP SSL) | Fetching emails + attachments |
| PDF Parsing | PyMuPDF, pypdf | Text extraction from PDFs |
| Doc Parsing | python-docx, unstructured | Word docs + other formats |
| Database | PostgreSQL + SQLAlchemy | Duplicate claim detection |
| PDF Generation | WeasyPrint + Jinja2 | Professional report output |
| Backend API | FastAPI + Uvicorn | REST API layer |
| Real-time | websockets | Live UI updates |
| UI | Streamlit | Dashboard frontend |

---

## Setup & Installation

### Prerequisites
- Python 3.12+
- PostgreSQL database (or [Neon](https://neon.tech) cloud account)
- OpenAI API key
- Gmail account with **IMAP enabled** and an **App Password**

### 1. Clone & enter the repo
```bash
git clone <repo-url>
cd hacknovators-main
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Fill in all required values (see below)
```

---

## Environment Variables

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Gmail (IMAP) — use an App Password, not your login password
EMAIL_HOST=imap.gmail.com
EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx

# PostgreSQL database
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# WebSocket server
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765

# Run mode: "standalone" (one-shot) or "websocket" (with UI)
RUN_MODE=standalone

# FastAPI
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

> **Gmail App Password:** Google Account → Security → 2-Step Verification → App Passwords → Generate for "Mail". Also enable IMAP in Gmail Settings → Forwarding and POP/IMAP.

---

## Running the System

### Option A — Standalone (one-shot, no UI)
```bash
python main.py
```
Processes the latest email from the configured cedant and prints results.

### Option B — WebSocket Server + Streamlit UI
```bash
# Terminal 1 — WebSocket backend
python websocket_server.py

# Terminal 2 — Streamlit dashboard
streamlit run ui/main.py
# or: python run_ui.py
```
Then open http://localhost:8501 in your browser.

### Option C — Everything at once
```bash
python run_enhanced_system.py
```

### Option D — FastAPI REST backend only
```bash
python run.py
# API at http://localhost:8000/docs
```

---

## Output

After a successful run:

**PDF Report** saved to `reports/claims_report_<timestamp>.pdf`:
- Executive summary
- Per-check findings (fraud, exclusions, reconciliation, dates, duplicates, compliance)
- Final recommendation with justification
- Critical issues list
- Recommended next steps

**Final Recommendation** — one of:
- ✅ `APPROVE` — All checks passed, proceed with payment
- ❌ `REJECT` — Critical violations found, prepare rejection notice
- ⚠️  `REVIEW` — Ambiguous findings, escalate to supervisor

**Critical Issues** (when flagged):
- `HIGH FRAUD RISK` — Immediate supervisor review required
- `TREATY EXCLUSION VIOLATIONS` — Claims may be rejected
- `DUPLICATE CLAIMS DETECTED` — Verify claim uniqueness
- `AMOUNT DISCREPANCIES` — Manual reconciliation required

---

## Key Design Decisions

- **Multi-agent architecture** — Document handling, analysis, and report generation are separate agents with independent lifecycles, statuses, and error handling.
- **FAISS vector store** — All document text is embedded so the LangChain agent can semantically retrieve relevant passages without re-reading entire files on each query.
- **ReAct agent pattern** — The analysis agent reasons step-by-step, choosing which tool to invoke based on what it has already found — mirroring how a human auditor would work through a claim.
- **WebSocket real-time updates** — Every stage transition, tool call, and analysis result is broadcast instantly so the UI never needs to poll.
- **Async throughout** — All agents use `asyncio` to stay responsive during long-running LLM and I/O operations.
