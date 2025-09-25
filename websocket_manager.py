import asyncio
import json
import logging
from typing import Set, Dict, Any
import websockets
from websockets.server import WebSocketServerProtocol

class WebSocketManager:
    
    def __init__(self):
        self.connections: Set[WebSocketServerProtocol] = set()
        self.logger = logging.getLogger(__name__)
    
    async def register(self, websocket: WebSocketServerProtocol):
        self.connections.add(websocket)
        self.logger.info(f"Client connected. Total connections: {len(self.connections)}")
        
        await websocket.send(json.dumps({
            "type": "connection_established",
            "message": "Connected to Claims Processing Agent",
            "timestamp": asyncio.get_event_loop().time()
        }))
    
    async def unregister(self, websocket: WebSocketServerProtocol):
        self.connections.remove(websocket)
        self.logger.info(f"Client disconnected. Total connections: {len(self.connections)}")
    
    async def broadcast(self, message: str):
        if not self.connections:
            return
        
        disconnected = set()
        
        for websocket in self.connections:
            try:
                await websocket.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)
        
        for websocket in disconnected:
            self.connections.discard(websocket)
    
    async def send_to_client(self, websocket: WebSocketServerProtocol, message: Dict[str, Any]):
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            self.connections.discard(websocket)
        except Exception as e:
            self.logger.error(f"Error sending message to client: {e}")
    
    def get_connection_count(self) -> int:
        return len(self.connections)

websocket_manager = WebSocketManager()