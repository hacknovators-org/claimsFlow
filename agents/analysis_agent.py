import os
from typing import Dict, Any, List
from langchain.agents import create_react_agent, AgentExecutor, initialize_agent, AgentType
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from sqlalchemy import create_engine
from .base_agent import BaseAgent, AgentStatus
from services.agent_tools import (
    initialize_tools, query_documents, extract_treaty_exclusions,
    validate_claim_against_exclusions, extract_bordereaux_claims,
    extract_statement_totals, compare_bordereaux_vs_statement,
    validate_claim_dates, check_duplicate_claims_in_database,
    extract_notification_details, validate_accounting_quarter,
    calculate_recovery_amounts
)
import asyncio
import time

class ClaimsAnalysisAgent(BaseAgent):
    
    def __init__(self, agent_id: str, websocket_manager=None):
        super().__init__(agent_id, websocket_manager)
        self.llm = None
        self.agent_executor = None
        self.vector_store = None
        self.tools = []
        self.analysis_results = {}
    
    async def execute(self, vector_store_path: str, email_analysis: Dict) -> Dict[str, Any]:
        try:
            self.status = AgentStatus.PROCESSING
            await self.send_update("initialization", "Initializing claims analysis agent", 5.0)
            await asyncio.sleep(0.5)
            
            await self._initialize_agent(vector_store_path)
            
            await self.send_update("document_query", "Querying documents for claims data", 15.0)
            await asyncio.sleep(0.3)
            claims_data = await self._extract_claims_data()
            
            await self.send_update("fraud_detection", "Running advanced fraud detection analysis", 25.0)
            await asyncio.sleep(0.3)
            fraud_analysis = await self._run_fraud_detection(claims_data)
            
            await self.send_update("exclusion_check", "Validating claims against treaty exclusions", 35.0)
            await asyncio.sleep(0.3)
            exclusion_analysis = await self._check_exclusions(claims_data)
            
            await self.send_update("amount_reconciliation", "Reconciling amounts between documents", 45.0)
            await asyncio.sleep(0.3)
            reconciliation_results = await self._reconcile_amounts()
            
            await self.send_update("date_validation", "Validating claim dates and policy periods", 55.0)
            await asyncio.sleep(0.3)
            date_validation = await self._validate_dates(claims_data)
            
            await self.send_update("duplicate_check", "Checking for duplicate claims in database", 65.0)
            await asyncio.sleep(0.3)
            duplicate_check = await self._check_duplicates(claims_data)
            
            await self.send_update("compliance_validation", "Running regulatory compliance checks", 75.0)
            await asyncio.sleep(0.3)
            compliance_results = await self._validate_compliance()
            
            await self.send_update("final_assessment", "Generating comprehensive final assessment", 85.0)
            await asyncio.sleep(0.3)
            final_assessment = await self._generate_final_assessment()
            
            self.status = AgentStatus.COMPLETED
            self.results = {
                "claims_data": claims_data,
                "fraud_analysis": fraud_analysis,
                "exclusion_analysis": exclusion_analysis,
                "reconciliation_results": reconciliation_results,
                "date_validation": date_validation,
                "duplicate_check": duplicate_check,
                "compliance_results": compliance_results,
                "final_assessment": final_assessment,
                "overall_recommendation": self._determine_recommendation()
            }
            
            await self.send_update("completion", "Claims analysis completed successfully", 100.0)
            
            return self.results
            
        except Exception as e:
            error_msg = f"Claims analysis failed: {str(e)}"
            await self.send_update("error", error_msg, self.progress, error=error_msg)
            raise
    
    async def _initialize_agent(self, vector_store_path: str):
        await self.send_tool_update("environment_setup", "Setting up OpenAI and database connections", "executing")
        
        openai_api_key = os.getenv("OPENAI_API_KEY")
        database_url = os.getenv("DATABASE_URL")
        
        if not openai_api_key:
            raise Exception("OPENAI_API_KEY not found in environment")
        
        self.llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key, temperature=0)
        
        await self.send_tool_update("vector_store_loading", "Loading document embeddings", "executing")
        embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
        
        if database_url:
            await self.send_tool_update("database_connection", "Connecting to claims database", "executing")
            initialize_tools(self.vector_store, database_url, openai_api_key)
        
        await self.send_tool_update("agent_tools_setup", "Configuring analysis tools", "executing")
        self.tools = [
            query_documents,
            extract_treaty_exclusions,
            validate_claim_against_exclusions,
            extract_bordereaux_claims,
            extract_statement_totals,
            compare_bordereaux_vs_statement,
            validate_claim_dates,
            check_duplicate_claims_in_database,
            extract_notification_details,
            validate_accounting_quarter,
            calculate_recovery_amounts
        ]
        
        self.agent_executor = initialize_agent(
        tools=self.tools,
        llm=self.llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
        agent_kwargs={
            "prefix": """You are a professional reinsurance claims analyst. Use the available tools to thoroughly analyze the claims documents.
            
            Your analysis should cover:
            1. Document completeness and data extraction
            2. Fraud detection and risk assessment
            3. Treaty compliance and exclusions validation
            4. Amount reconciliation between bordereaux and statements
            5. Date validations and policy period compliance
            6. Duplicate claims detection
            7. Regulatory compliance checks
            
            Always provide detailed reasoning for your conclusions and recommendations."""
        }
    )
        
        await self.send_tool_update("agent_tools_setup", "Analysis tools configured successfully", "completed")
    
    async def _extract_claims_data(self) -> Dict[str, Any]:
        try:
            await self.send_tool_update("extract_bordereaux_claims", "Extracting claims data from bordereaux documents", "executing")
            await asyncio.sleep(1)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Extract all claims-related data from the documents. Look for:
                1. Claims notifications with claim numbers, policy numbers, loss dates
                2. Bordereaux entries with paid amounts and outstanding amounts
                3. Statement totals and reconciliation figures
                4. Any claim-specific details like insured names, loss descriptions
                
                Organize this data in a structured format for analysis.
                """
            })
            
            await self.send_tool_update("extract_bordereaux_claims", "Claims data extraction completed", "completed")
            await self.send_analysis_update("data_extraction", "Successfully extracted claims data from documents")
            
            return {
                "extraction_successful": True,
                "agent_response": response.get("output", ""),
                "raw_data": response
            }
        except Exception as e:
            await self.send_tool_update("extract_bordereaux_claims", f"Claims data extraction failed: {str(e)}", "failed")
            return {
                "extraction_successful": False,
                "error": str(e),
                "agent_response": ""
            }
    
    async def _run_fraud_detection(self, claims_data: Dict) -> Dict[str, Any]:
        try:
            await self.send_tool_update("fraud_analysis", "Analyzing claims for fraud indicators", "executing")
            await asyncio.sleep(1.5)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Analyze the extracted claims data for potential fraud indicators:
                1. Unusual claim amounts or patterns
                2. Claims close to policy expiry dates
                3. Multiple claims from same insured within short periods
                4. Claims with incomplete or suspicious documentation
                5. Amount discrepancies between different documents
                
                Rate the fraud risk as LOW, MEDIUM, or HIGH with detailed justification.
                """
            })
            
            risk_level = self._extract_risk_level(response.get("output", ""))
            await self.send_tool_update("fraud_analysis", f"Fraud analysis completed - Risk Level: {risk_level}", "completed")
            await self.send_analysis_update("fraud_detection", f"Fraud risk assessment: {risk_level}", risk_level)
            
            return {
                "fraud_analysis_completed": True,
                "agent_response": response.get("output", ""),
                "risk_level": risk_level,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("fraud_analysis", f"Fraud analysis failed: {str(e)}", "failed")
            return {
                "fraud_analysis_completed": False,
                "error": str(e),
                "risk_level": "UNKNOWN"
            }
    
    async def _check_exclusions(self, claims_data: Dict) -> Dict[str, Any]:
        try:
            await self.send_tool_update("validate_claim_against_exclusions", "Checking claims against treaty exclusions", "executing")
            await asyncio.sleep(1.2)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Check all claims against treaty exclusions:
                1. Extract treaty exclusions from contract documents
                2. Validate each claim against these exclusions
                3. Identify any claims that should be excluded
                4. Provide detailed reasoning for exclusion recommendations
                
                Focus on common exclusions like war, nuclear, cyber, pollution, etc.
                """
            })
            
            violations_found = "violation" in response.get("output", "").lower()
            status = "violations detected" if violations_found else "no violations found"
            await self.send_tool_update("validate_claim_against_exclusions", f"Exclusion validation completed - {status}", "completed")
            
            risk_level = "HIGH" if violations_found else "LOW"
            await self.send_analysis_update("exclusion_check", f"Treaty exclusion validation: {status}", risk_level)
            
            return {
                "exclusion_check_completed": True,
                "agent_response": response.get("output", ""),
                "violations_found": violations_found,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("validate_claim_against_exclusions", f"Exclusion validation failed: {str(e)}", "failed")
            return {
                "exclusion_check_completed": False,
                "error": str(e),
                "violations_found": False
            }
    
    async def _reconcile_amounts(self) -> Dict[str, Any]:
        try:
            await self.send_tool_update("compare_bordereaux_vs_statement", "Reconciling amounts between documents", "executing")
            await asyncio.sleep(1.3)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Reconcile amounts between different documents:
                1. Compare bordereaux totals with statement totals
                2. Check if paid losses match across documents
                3. Validate outstanding amounts consistency
                4. Identify any material discrepancies (>5% variance)
                5. Compare booked amounts with cash call records
                
                Provide detailed reconciliation summary with variance analysis.
                """
            })
            
            discrepancies_found = "discrepancy" in response.get("output", "").lower()
            status = "discrepancies found" if discrepancies_found else "amounts reconciled"
            await self.send_tool_update("compare_bordereaux_vs_statement", f"Amount reconciliation completed - {status}", "completed")
            
            risk_level = "MEDIUM" if discrepancies_found else "LOW"
            await self.send_analysis_update("amount_reconciliation", f"Amount reconciliation: {status}", risk_level)
            
            return {
                "reconciliation_completed": True,
                "agent_response": response.get("output", ""),
                "discrepancies_found": discrepancies_found,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("compare_bordereaux_vs_statement", f"Amount reconciliation failed: {str(e)}", "failed")
            return {
                "reconciliation_completed": False,
                "error": str(e),
                "discrepancies_found": True
            }
    
    async def _validate_dates(self, claims_data: Dict) -> Dict[str, Any]:
        try:
            await self.send_tool_update("validate_claim_dates", "Validating claim dates and policy periods", "executing")
            await asyncio.sleep(1.1)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Validate all claim dates:
                1. Check if loss dates fall within policy periods
                2. Ensure payment dates are within the correct accounting quarter
                3. Validate notification dates are reasonable after loss dates
                4. Check for any date inconsistencies across documents
                
                Report any date validation failures with specific details.
                """
            })
            
            validation_failures = "fail" in response.get("output", "").lower()
            status = "validation failures detected" if validation_failures else "all dates valid"
            await self.send_tool_update("validate_claim_dates", f"Date validation completed - {status}", "completed")
            
            risk_level = "MEDIUM" if validation_failures else "LOW"
            await self.send_analysis_update("date_validation", f"Date validation: {status}", risk_level)
            
            return {
                "date_validation_completed": True,
                "agent_response": response.get("output", ""),
                "validation_failures": validation_failures,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("validate_claim_dates", f"Date validation failed: {str(e)}", "failed")
            return {
                "date_validation_completed": False,
                "error": str(e),
                "validation_failures": True
            }
    
    async def _check_duplicates(self, claims_data: Dict) -> Dict[str, Any]:
        try:
            await self.send_tool_update("check_duplicate_claims_in_database", "Checking for duplicate claims in database", "executing")
            await asyncio.sleep(1.4)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Check for duplicate claims:
                1. Search database for existing claims with same claim IDs
                2. Look for similar claims from same insured with same loss dates
                3. Check for potential double-billing scenarios
                4. Validate uniqueness of claim references across all documents
                
                Report any duplicate claims found with detailed evidence.
                """
            })
            
            duplicates_found = "duplicate" in response.get("output", "").lower()
            status = "duplicates detected" if duplicates_found else "no duplicates found"
            await self.send_tool_update("check_duplicate_claims_in_database", f"Duplicate check completed - {status}", "completed")
            
            risk_level = "HIGH" if duplicates_found else "LOW"
            await self.send_analysis_update("duplicate_check", f"Duplicate claims check: {status}", risk_level)
            
            return {
                "duplicate_check_completed": True,
                "agent_response": response.get("output", ""),
                "duplicates_found": duplicates_found,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("check_duplicate_claims_in_database", f"Duplicate check failed: {str(e)}", "failed")
            return {
                "duplicate_check_completed": False,
                "error": str(e),
                "duplicates_found": False
            }
    
    async def _validate_compliance(self) -> Dict[str, Any]:
        try:
            await self.send_tool_update("compliance_validation", "Running regulatory compliance checks", "executing")
            await asyncio.sleep(1.6)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Perform comprehensive compliance validation:
                1. Check regulatory compliance for marine claims processing
                2. Validate adherence to treaty terms and conditions
                3. Ensure proper documentation standards are met
                4. Verify authorization levels for claim amounts
                5. Check compliance with accounting standards
                
                Provide compliance score and highlight any violations.
                """
            })
            
            compliance_issues = "violation" in response.get("output", "").lower() or "non-compliant" in response.get("output", "").lower()
            status = "compliance issues detected" if compliance_issues else "fully compliant"
            await self.send_tool_update("compliance_validation", f"Compliance validation completed - {status}", "completed")
            
            risk_level = "HIGH" if compliance_issues else "LOW"
            await self.send_analysis_update("compliance_validation", f"Regulatory compliance: {status}", risk_level)
            
            return {
                "compliance_validation_completed": True,
                "agent_response": response.get("output", ""),
                "compliance_issues": compliance_issues,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("compliance_validation", f"Compliance validation failed: {str(e)}", "failed")
            return {
                "compliance_validation_completed": False,
                "error": str(e),
                "compliance_issues": True
            }
    
    async def _generate_final_assessment(self) -> Dict[str, Any]:
        try:
            await self.send_tool_update("final_assessment", "Generating comprehensive final assessment", "executing")
            await asyncio.sleep(2)
            
            response = await self.agent_executor.ainvoke({
                "input": """
                Generate a comprehensive final assessment based on all previous analyses:
                1. Summarize key findings from each validation step
                2. Assess overall claim validity and processing readiness
                3. Identify critical issues requiring supervisor review
                4. Provide clear recommendation: APPROVE, REJECT, or REVIEW
                5. List specific actions needed before claim processing
                
                Structure this as an executive summary suitable for management review.
                """
            })
            
            recommendation = self._extract_recommendation(response.get("output", ""))
            await self.send_tool_update("final_assessment", f"Final assessment completed - Recommendation: {recommendation}", "completed")
            await self.send_analysis_update("final_assessment", f"Final recommendation: {recommendation}", 
                                          "HIGH" if recommendation == "REJECT" else "MEDIUM" if recommendation == "REVIEW" else "LOW")
            
            return {
                "final_assessment_completed": True,
                "agent_response": response.get("output", ""),
                "recommendation": recommendation,
                "raw_analysis": response
            }
        except Exception as e:
            await self.send_tool_update("final_assessment", f"Final assessment failed: {str(e)}", "failed")
            return {
                "final_assessment_completed": False,
                "error": str(e),
                "recommendation": "REVIEW"
            }
    
    def _extract_risk_level(self, response: str) -> str:
        response_lower = response.lower()
        if "high" in response_lower:
            return "HIGH"
        elif "medium" in response_lower:
            return "MEDIUM"
        elif "low" in response_lower:
            return "LOW"
        return "MEDIUM"
    
    def _extract_recommendation(self, response: str) -> str:
        response_lower = response.lower()
        if "approve" in response_lower:
            return "APPROVE"
        elif "reject" in response_lower:
            return "REJECT"
        return "REVIEW"
    
    def _determine_recommendation(self) -> str:
        fraud_risk = self.results.get("fraud_analysis", {}).get("risk_level", "UNKNOWN")
        exclusions_violated = self.results.get("exclusion_analysis", {}).get("violations_found", False)
        discrepancies = self.results.get("reconciliation_results", {}).get("discrepancies_found", False)
        duplicates = self.results.get("duplicate_check", {}).get("duplicates_found", False)
        date_failures = self.results.get("date_validation", {}).get("validation_failures", False)
        compliance_issues = self.results.get("compliance_results", {}).get("compliance_issues", False)
        
        if any([exclusions_violated, duplicates, fraud_risk == "HIGH"]):
            return "REJECT"
        elif any([discrepancies, date_failures, compliance_issues, fraud_risk == "MEDIUM"]):
            return "REVIEW"
        elif fraud_risk == "LOW" and not any([discrepancies, date_failures, compliance_issues]):
            return "APPROVE"
        else:
            return "REVIEW"