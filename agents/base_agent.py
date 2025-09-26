from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from datetime import datetime
import time

class AgentStatus(Enum):
    INITIALIZED = "initialized"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class AgentUpdate:
    agent_id: str
    timestamp: datetime
    status: AgentStatus
    stage: str
    message: str
    progress: float
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class BaseAgent(ABC):
    
    def __init__(self, agent_id: str, websocket_manager=None):
        self.agent_id = agent_id
        self.websocket_manager = websocket_manager
        self.status = AgentStatus.INITIALIZED
        self.current_stage = ""
        self.progress = 0.0
        self.results = {}
        self.errors = []
        self.stage_start_time = None
    
    async def send_update(self, stage: str, message: str, progress: float, data: Dict = None, error: str = None):
        if error:
            self.status = AgentStatus.FAILED
            self.errors.append(error)
        
        if self.current_stage != stage:
            if self.stage_start_time and self.websocket_manager:
                duration = time.time() - self.stage_start_time
                await self.websocket_manager.send_stage_completion(
                    self.agent_id, self.current_stage, duration, success=not error
                )
            self.stage_start_time = time.time()
        
        self.current_stage = stage
        self.progress = progress
        
        update = AgentUpdate(
            agent_id=self.agent_id,
            timestamp=datetime.utcnow(),
            status=self.status,
            stage=stage,
            message=message,
            progress=progress,
            data=data,
            error=error
        )
        
        if self.websocket_manager:
            await self.websocket_manager.send_progress_update(
                agent_id=update.agent_id,
                stage=update.stage,
                message=update.message,
                progress=update.progress,
                data=update.data,
                error=update.error
            )
    
    async def send_tool_update(self, tool_name: str, tool_description: str, status: str = "executing"):
        if self.websocket_manager:
            await self.websocket_manager.send_tool_execution(
                agent_id=self.agent_id,
                tool_name=tool_name,
                tool_description=tool_description,
                status=status
            )
    
    async def send_analysis_update(self, analysis_type: str, result: str, risk_level: str = "LOW"):
        if self.websocket_manager:
            await self.websocket_manager.send_analysis_result(
                agent_id=self.agent_id,
                analysis_type=analysis_type,
                result=result,
                risk_level=risk_level
            )
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_stage": self.current_stage,
            "progress": self.progress,
            "results": self.results,
            "errors": self.errors
        }