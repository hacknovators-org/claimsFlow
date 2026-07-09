import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

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

app = FastAPI(title="Claims Flow SMS Gateway")
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
