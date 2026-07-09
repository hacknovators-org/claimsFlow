# Claims Flow — Frontend

React + TypeScript SPA for the claims processing dashboard, talking to the
FastAPI backend over REST (`/processing/*`) and a shared WebSocket (`/ws`).
See [`../docs/01-architecture-decision.md`](../docs/01-architecture-decision.md)
for the full design.

## Local development

Run the backend and frontend as two separate processes:

```bash
# Terminal 1, from the repo root
uvicorn main:app --reload

# Terminal 2
cd frontend
npm install
npm run dev
```

The Vite dev server runs at `http://localhost:5173` and talks to the API at
`http://localhost:8000` (see `.env.development`). The backend's
`FRONTEND_ORIGINS` env var must include `http://localhost:5173` for CORS —
this is the default if unset.

## Production build

```bash
npm run build   # outputs frontend/dist/
```

Once `frontend/dist/` exists, `uvicorn main:app` serves the built SPA
directly from the same origin as the API (no CORS needed) — see
[`../docs/05-testing-deployment-cutover.md`](../docs/05-testing-deployment-cutover.md)
§Deployment.
