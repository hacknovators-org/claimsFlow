import logging
from typing import Set

from starlette.websockets import WebSocket, WebSocketDisconnect


class WebSocketManager:

    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.logger = logging.getLogger(__name__)

    async def register(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        self.logger.info(f"Client connected. Total connections: {len(self.connections)}")

    async def unregister(self, websocket: WebSocket):
        self.connections.discard(websocket)
        self.logger.info(f"Client disconnected. Total connections: {len(self.connections)}")

    async def broadcast(self, message: str):
        if not self.connections:
            return

        disconnected = set()

        for websocket in self.connections:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)

        for websocket in disconnected:
            self.connections.discard(websocket)

    def get_connection_count(self) -> int:
        return len(self.connections)


websocket_manager = WebSocketManager()
