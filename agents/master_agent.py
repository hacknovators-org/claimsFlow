import asyncio
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentStatus
from .document_agent import DocumentAgent
from .analysis_agent import ClaimsAnalysisAgent
from .report_agent import ReportGenerationAgent

class MasterClaimsAgent(BaseAgent):
    
    def __init__(self, agent_id: str, websocket_manager=None):
        super().__init__(agent_id, websocket_manager)
        self.document_agent = None
        self.analysis_agent = None
        self.report_agent = None
        self.sub_agents = {}
    
    async def execute(self, sender_email: str = "Maundu@kenyare.co.ke") -> Dict[str, Any]:
        try:
            self.status = AgentStatus.PROCESSING
            await self.send_update("initialization", "Initializing master claims processing agent", 2.0)
            
            await self.send_update("document_processing", "Starting document processing phase", 5.0)
            document_results = await self._run_document_processing(sender_email)
            
            await self.send_update("claims_analysis", "Starting claims analysis phase", 35.0)
            analysis_results = await self._run_claims_analysis(document_results)
            
            await self.send_update("report_generation", "Starting report generation phase", 70.0)
            report_results = await self._run_report_generation(analysis_results, document_results)
            
            await self.send_update("finalization", "Finalizing results", 95.0)
            final_results = await self._finalize_results(document_results, analysis_results, report_results)
            
            self.status = AgentStatus.COMPLETED
            self.results = final_results
            
            await self.send_update("completion", "Claims processing completed successfully", 100.0, 
                                 data={"final_recommendation": final_results.get("overall_recommendation")})
            
            return self.results
            
        except Exception as e:
            error_msg = f"Master agent execution failed: {str(e)}"
            await self.send_update("error", error_msg, self.progress, error=error_msg)
            raise
    
    async def _run_document_processing(self, sender_email: str) -> Dict[str, Any]:
        self.document_agent = DocumentAgent(f"{self.agent_id}_document", self.websocket_manager)
        self.sub_agents["document"] = self.document_agent
        
        try:
            return await self.document_agent.execute(sender_email)
        except Exception as e:
            raise Exception(f"Document processing failed: {str(e)}")
    
    async def _run_claims_analysis(self, document_results: Dict[str, Any]) -> Dict[str, Any]:
        self.analysis_agent = ClaimsAnalysisAgent(f"{self.agent_id}_analysis", self.websocket_manager)
        self.sub_agents["analysis"] = self.analysis_agent
        
        try:
            vector_store_path = document_results.get("vector_store_path")
            email_analysis = document_results.get("email_analysis", {})
            
            return await self.analysis_agent.execute(vector_store_path, email_analysis)
        except Exception as e:
            raise Exception(f"Claims analysis failed: {str(e)}")
    
    async def _run_report_generation(self, analysis_results: Dict[str, Any], document_results: Dict[str, Any]) -> Dict[str, Any]:
        self.report_agent = ReportGenerationAgent(f"{self.agent_id}_report", self.websocket_manager)
        self.sub_agents["report"] = self.report_agent
        
        try:
            return await self.report_agent.execute(analysis_results, document_results)
        except Exception as e:
            raise Exception(f"Report generation failed: {str(e)}")
    
    async def _finalize_results(self, document_results: Dict[str, Any], analysis_results: Dict[str, Any], report_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "master_agent_id": self.agent_id,
            "processing_status": "COMPLETED",
            "overall_recommendation": analysis_results.get("overall_recommendation", "REVIEW"),
            "fraud_risk_level": analysis_results.get("fraud_analysis", {}).get("risk_level", "UNKNOWN"),
            "document_processing": {
                "status": "COMPLETED",
                "files_processed": len(document_results.get("downloaded_files", [])),
                "email_completeness": document_results.get("email_analysis", {}).get("completion_status", "Unknown"),
                "missing_documents": document_results.get("email_analysis", {}).get("missing_documents", [])
            },
            "analysis_summary": {
                "fraud_analysis_completed": analysis_results.get("fraud_analysis", {}).get("fraud_analysis_completed", False),
                "exclusion_check_completed": analysis_results.get("exclusion_analysis", {}).get("exclusion_check_completed", False),
                "reconciliation_completed": analysis_results.get("reconciliation_results", {}).get("reconciliation_completed", False),
                "date_validation_completed": analysis_results.get("date_validation", {}).get("date_validation_completed", False),
                "duplicate_check_completed": analysis_results.get("duplicate_check", {}).get("duplicate_check_completed", False),
                "compliance_validation_completed": analysis_results.get("compliance_results", {}).get("compliance_validation_completed", False)
            },
            "critical_issues": self._identify_critical_issues(analysis_results),
            "report_generated": {
                "pdf_path": report_results.get("pdf_report_path"),
                "generation_timestamp": report_results.get("generation_timestamp"),
                "executive_summary": report_results.get("executive_summary")
            },
            "next_steps": self._determine_next_steps(analysis_results),
            "processing_metadata": {
                "email_sender": document_results.get("email_content", {}).get("sender"),
                "email_subject": document_results.get("email_content", {}).get("subject"),
                "total_processing_agents": len(self.sub_agents),
                "agent_statuses": {name: agent.status.value for name, agent in self.sub_agents.items()}
            }
        }
    
    def _identify_critical_issues(self, analysis_results: Dict[str, Any]) -> List[str]:
        critical_issues = []
        
        if analysis_results.get("fraud_analysis", {}).get("risk_level") == "HIGH":
            critical_issues.append("HIGH FRAUD RISK - Immediate supervisor review required")
        
        if analysis_results.get("exclusion_analysis", {}).get("violations_found"):
            critical_issues.append("TREATY EXCLUSION VIOLATIONS - Claims may be rejected")
        
        if analysis_results.get("duplicate_check", {}).get("duplicates_found"):
            critical_issues.append("DUPLICATE CLAIMS DETECTED - Verify uniqueness")
        
        if analysis_results.get("reconciliation_results", {}).get("discrepancies_found"):
            critical_issues.append("AMOUNT DISCREPANCIES - Reconciliation required")
        
        return critical_issues
    
    def _determine_next_steps(self, analysis_results: Dict[str, Any]) -> List[str]:
        recommendation = analysis_results.get("overall_recommendation", "REVIEW")
        next_steps = []
        
        if recommendation == "APPROVE":
            next_steps.extend([
                "Proceed with standard claims processing workflow",
                "Generate payment authorization documents",
                "Update claims management system",
                "Notify cedant of approval"
            ])
        elif recommendation == "REJECT":
            next_steps.extend([
                "Prepare formal rejection notice with detailed reasons",
                "Schedule meeting with cedant to discuss findings",
                "Escalate to senior management for final approval",
                "Update claims system with rejection status"
            ])
        else:  # REVIEW
            next_steps.extend([
                "Schedule immediate supervisor review meeting",
                "Prepare detailed analysis for management review",
                "Request additional documentation if required",
                "Hold processing pending management decision"
            ])
        
        return next_steps
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        status = self.get_status()
        
        sub_agent_statuses = {}
        for name, agent in self.sub_agents.items():
            sub_agent_statuses[name] = agent.get_status()
        
        status["sub_agents"] = sub_agent_statuses
        return status
    
    async def stop_processing(self):
        self.status = AgentStatus.PAUSED
        await self.send_update("stopping", "Processing stopped by user", self.progress)