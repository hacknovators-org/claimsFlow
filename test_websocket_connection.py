"""
Test script to verify the FastAPI /ws broadcast connection.
Run this against a live `uvicorn main:app` process (see run.py) while a
processing run is active to watch AgentUpdate JSON messages arrive.
"""
import asyncio
import json
import logging
import os

import websockets
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    host = os.getenv("HOST", "localhost").replace("0.0.0.0", "localhost")
    port = os.getenv("PORT", 8000)
    uri = f"ws://{host}:{port}/ws"

    try:
        logger.info(f"Testing connection to {uri}...")

        async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
            logger.info("Successfully connected to /ws")
            logger.info("Listening for AgentUpdate broadcasts (Ctrl+C to stop)...")

            while True:
                message = await websocket.recv()
                update = json.loads(message)
                logger.info(
                    f"[{update.get('agent_id')}] {update.get('stage')} "
                    f"({update.get('progress')}%) - {update.get('message')}"
                )

    except ConnectionRefusedError:
        logger.error("Connection refused. Is `uvicorn main:app` (run.py) running?")
        return False
    except KeyboardInterrupt:
        return True
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_connection())
