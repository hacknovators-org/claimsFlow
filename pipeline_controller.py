import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from agents.master_agent import MasterClaimsAgent
from websocket_manager import WebSocketManager

class ClaimsProcessingPipeline:
    
    def __init__(self, websocket_manager: Optional[WebSocketManager] = None):
        self.websocket_manager = websocket_manager
        self.active_agents: Dict[str, MasterClaimsAgent] = {}
        self.processing_history = []
        self.logger = logging.getLogger(__name__)
    
    async def start_processing(self, sender_email: str = "Maundu@kenyare.co.ke") -> Dict[str, Any]:
        agent_id = f"claims_agent_{uuid.uuid4().hex[:8]}"
        
        try:
            self.logger.info(f"Starting claims processing with agent ID: {agent_id}")
            
            master_agent = MasterClaimsAgent(agent_id, self.websocket_manager)
            self.active_agents[agent_id] = master_agent
            
            processing_start = datetime.utcnow()
            
            if self.websocket_manager:
                await self.websocket_manager.broadcast(f"Starting claims processing for {sender_email}")
            
            results = await master_agent.execute(sender_email)
            
            processing_end = datetime.utcnow()
            processing_duration = (processing_end - processing_start).total_seconds()
            
            processing_record = {
                "agent_id": agent_id,
                "sender_email": sender_email,
                "start_time": processing_start.isoformat(),
                "end_time": processing_end.isoformat(),
                "duration_seconds": processing_duration,
                "status": "COMPLETED",
                "recommendation": results.get("overall_recommendation"),
                "critical_issues_count": len(results.get("critical_issues", [])),
                "report_path": results.get("report_generated", {}).get("pdf_path")
            }
            
            self.processing_history.append(processing_record)
            
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
            
            self.logger.info(f"Claims processing completed successfully: {agent_id}")
            
            return {
                "success": True,
                "agent_id": agent_id,
                "processing_duration": processing_duration,
                "results": results,
                "processing_record": processing_record
            }
            
        except Exception as e:
            error_msg = f"Claims processing failed: {str(e)}"
            self.logger.error(f"Agent {agent_id}: {error_msg}")
            
            if agent_id in self.active_agents:
                del self.active_agents[agent_id]
            
            processing_record = {
                "agent_id": agent_id,
                "sender_email": sender_email,
                "start_time": processing_start.isoformat() if 'processing_start' in locals() else datetime.utcnow().isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "status": "FAILED",
                "error": error_msg
            }
            
            self.processing_history.append(processing_record)
            
            if self.websocket_manager:
                await self.websocket_manager.broadcast(f"Claims processing failed: {error_msg}")
            
            return {
                "success": False,
                "agent_id": agent_id,
                "error": error_msg,
                "processing_record": processing_record
            }
    
    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        if agent_id in self.active_agents:
            return await self.active_agents[agent_id].get_comprehensive_status()
        return None
    
    async def stop_agent(self, agent_id: str) -> bool:
        if agent_id in self.active_agents:
            await self.active_agents[agent_id].stop_processing()
            del self.active_agents[agent_id]
            return True
        return False
    
    def get_active_agents(self) -> List[str]:
        return list(self.active_agents.keys())
    
    def get_processing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.processing_history[-limit:]
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        total_processed = len(self.processing_history)
        successful = len([r for r in self.processing_history if r.get("status") == "COMPLETED"])
        failed = len([r for r in self.processing_history if r.get("status") == "FAILED"])
        
        avg_duration = 0
        if total_processed > 0:
            durations = [r.get("duration_seconds", 0) for r in self.processing_history if r.get("duration_seconds")]
            avg_duration = sum(durations) / len(durations) if durations else 0
        
        recommendations = {}
        for record in self.processing_history:
            rec = record.get("recommendation", "UNKNOWN")
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_processed * 100) if total_processed > 0 else 0,
            "active_agents": len(self.active_agents),
            "average_processing_time": avg_duration,
            "recommendations_breakdown": recommendations,
            "last_processing": self.processing_history[-1] if self.processing_history else None
        }