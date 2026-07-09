import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from websocket_manager import websocket_manager
from routes.sms import router as sms_router
from routes.processing import router as processing_router
from services.scheduler_service import start_scheduler

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

FRONTEND_ORIGINS = [o.strip() for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app = FastAPI(title="Claims Flow SMS Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(sms_router)
app.include_router(processing_router)


@app.on_event("startup")
async def _on_startup():
    validate_environment()
    start_scheduler()


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket_manager.register(websocket)
    try:
        while True:
            await websocket.receive_text()  # UI doesn't send anything but must keep the socket alive
    except WebSocketDisconnect:
        await websocket_manager.unregister(websocket)


# Production: FastAPI serves the built React SPA directly (single-origin,
# no CORS needed). Registered last so API routes above still take priority,
# and skipped entirely if the frontend hasn't been built yet (local API-only
# dev against `npm run dev`'s Vite server instead).
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def spa_catch_all(full_path: str):
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


def validate_environment():
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "EMAIL_HOST",
        "EMAIL_APP_PASSWORD"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    logger.info("Environment validation successful")
