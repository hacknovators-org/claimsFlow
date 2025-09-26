import asyncio
import json
import logging
from typing import Set, Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from datetime import datetime

class WebSocketManager:
    
    def __init__(self):
        self.connections: Set[WebSocketServerProtocol] = set()
        self.logger = logging.getLogger(__name__)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def register(self, websocket: WebSocketServerProtocol):
        self.connections.add(websocket)
        session_id = f"session_{len(self.connections)}_{datetime.now().timestamp()}"
        
        self.logger.info(f"Client connected. Total connections: {len(self.connections)}")
        
        await websocket.send(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "message": "Connected to Claims Processing Agent",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return session_id
    
    async def unregister(self, websocket: WebSocketServerProtocol):
        if websocket in self.connections:
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
    
    async def send_progress_update(self, agent_id: str, stage: str, message: str, 
                                 progress: float, data: Optional[Dict[str, Any]] = None, 
                                 error: Optional[str] = None):
        update = {
            "type": "agent_progress",
            "agent_id": agent_id,
            "stage": stage,
            "message": message,
            "progress": progress,
            "data": data or {},
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(json.dumps(update))
    
    async def send_tool_execution(self, agent_id: str, tool_name: str, tool_description: str, 
                                status: str = "executing"):
        update = {
            "type": "tool_execution",
            "agent_id": agent_id,
            "tool_name": tool_name,
            "tool_description": tool_description,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(json.dumps(update))
    
    async def send_stage_completion(self, agent_id: str, stage: str, duration: float, 
                                  success: bool = True, results: Optional[Dict] = None):
        update = {
            "type": "stage_completion",
            "agent_id": agent_id,
            "stage": stage,
            "duration": duration,
            "success": success,
            "results": results or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(json.dumps(update))
    
    async def send_analysis_result(self, agent_id: str, analysis_type: str, 
                                 result: str, risk_level: str = "LOW"):
        update = {
            "type": "analysis_result",
            "agent_id": agent_id,
            "analysis_type": analysis_type,
            "result": result,
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(json.dumps(update))
    
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