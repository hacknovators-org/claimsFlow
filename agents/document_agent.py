import os
from typing import Dict, Any, List
from pathlib import Path
import shutil
from .base_agent import BaseAgent, AgentStatus
from services.gmail_reader import FocusedGmailConnector
from services.email_analyzer import SimpleEmailAnalyzer
from services.agent import DocumentEmbeddingSystem
import asyncio

class DocumentAgent(BaseAgent):
    
    def __init__(self, agent_id: str, websocket_manager=None):
        super().__init__(agent_id, websocket_manager)
        self.gmail_connector = None
        self.email_analyzer = None
        self.embedding_system = None
        self.download_folder = "downloads"
        self.vector_store_path = "claims_vector_store"
    
    async def execute(self, sender_email: str = "Maundu@kenyare.co.ke") -> Dict[str, Any]:
        try:
            self.status = AgentStatus.PROCESSING
            await self.send_update("initialization", "Initializing document processing agent", 5.0)
            await asyncio.sleep(0.5)
            
            await self._initialize_services()
            
            await self.send_update("email_connection", "Connecting to Gmail and fetching emails", 10.0)
            await asyncio.sleep(0.3)
            email_content = await self._fetch_latest_email(sender_email)
            
            if not email_content:
                raise Exception(f"No emails found from {sender_email}")
            
            await self.send_update("attachment_download", "Downloading and processing email attachments", 20.0)
            await asyncio.sleep(0.3)
            downloaded_files = await self._download_attachments(email_content)
            
            if not downloaded_files:
                raise Exception("No attachments found in email")
            
            await self.send_update("document_preprocessing", "Analyzing document structure and content types", 35.0)
            await asyncio.sleep(0.5)
            document_analysis = await self._analyze_document_structure(downloaded_files)
            
            await self.send_update("email_analysis", "Performing enhanced email content analysis", 45.0)
            await asyncio.sleep(0.3)
            email_analysis = await self._analyze_email_enhanced(email_content, document_analysis)
            
            await self.send_update("document_processing", "Creating document embeddings and vector store", 60.0)
            await asyncio.sleep(0.8)
            vector_store = await self._create_embeddings(downloaded_files)
            
            await self.send_update("data_validation", "Validating document completeness and integrity", 80.0)
            await asyncio.sleep(0.3)
            validation_results = await self._validate_documents(email_analysis, downloaded_files, document_analysis)
            
            self.status = AgentStatus.COMPLETED
            self.results = {
                "email_content": {
                    "sender": email_content.sender,
                    "subject": email_content.subject,
                    "date": email_content.date,
                    "body_preview": email_content.body_text[:200]
                },
                "email_analysis": {
                    "completion_status": email_analysis.completion_status,
                    "all_documents_present": email_analysis.all_documents_present,
                    "missing_documents": email_analysis.missing_documents,
                    "documents_found": [
                        {
                            "filename": doc.filename,
                            "document_type": doc.document_type.value,
                            "confidence": doc.confidence
                        }
                        for doc in email_analysis.documents_found
                    ]
                },
                "document_analysis": document_analysis,
                "downloaded_files": downloaded_files,
                "vector_store_path": self.vector_store_path,
                "validation_results": validation_results
            }
            
            await self.send_update("completion", "Document processing completed successfully", 100.0, 
                                 data={"processed_files": len(downloaded_files)})
            
            return self.results
            
        except Exception as e:
            error_msg = f"Document processing failed: {str(e)}"
            await self.send_update("error", error_msg, self.progress, error=error_msg)
            raise
    
    async def _initialize_services(self):
        await self.send_tool_update("environment_setup", "Loading environment variables and API keys", "executing")
        
        email_host = os.getenv("EMAIL_HOST")
        email_password = os.getenv("EMAIL_APP_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([email_host, email_password, openai_api_key]):
            raise Exception("Missing required environment variables")
        
        await self.send_tool_update("service_initialization", "Initializing Gmail, Email Analyzer, and Embedding services", "executing")
        
        self.gmail_connector = FocusedGmailConnector(email_host, email_password)
        self.email_analyzer = SimpleEmailAnalyzer(openai_api_key)
        self.embedding_system = DocumentEmbeddingSystem(openai_api_key, self.download_folder)
        
        os.makedirs(self.download_folder, exist_ok=True)
        
        await self.send_tool_update("service_initialization", "All services initialized successfully", "completed")
    
    async def _fetch_latest_email(self, sender_email: str):
        await self.send_tool_update("gmail_connection", f"Connecting to Gmail and searching for emails from {sender_email}", "executing")
        
        with self.gmail_connector:
            latest_email = self.gmail_connector.read_latest_email_from_sender(sender_email)
            
        if latest_email:
            await self.send_tool_update("gmail_connection", f"Successfully retrieved email: {latest_email.subject}", "completed")
            await self.send_analysis_update("email_retrieval", f"Retrieved email from {sender_email} with subject: {latest_email.subject}")
        else:
            await self.send_tool_update("gmail_connection", f"No emails found from {sender_email}", "failed")
            
        return latest_email
    
    async def _download_attachments(self, email_content) -> List[str]:
        await self.send_tool_update("attachment_download", "Preparing download directory and extracting attachments", "executing")
        
        if Path(self.download_folder).exists():
            shutil.rmtree(self.download_folder)
        os.makedirs(self.download_folder, exist_ok=True)
        
        with self.gmail_connector:
            downloaded_files = self.gmail_connector.download_attachments(
                email_content, 
                download_folder=self.download_folder
            )
        
        if downloaded_files:
            await self.send_tool_update("attachment_download", f"Downloaded {len(downloaded_files)} attachments successfully", "completed")
            await self.send_analysis_update("attachment_processing", f"Downloaded {len(downloaded_files)} files: {[Path(f).name for f in downloaded_files]}")
        else:
            await self.send_tool_update("attachment_download", "No attachments found in email", "failed")
        
        return downloaded_files
    
    async def _analyze_document_structure(self, downloaded_files: List[str]) -> Dict[str, Any]:
        await self.send_tool_update("document_analysis", "Analyzing document structure and identifying document types", "executing")
        
        document_analysis = {
            "total_files": len(downloaded_files),
            "file_analysis": [],
            "detected_document_types": set(),
            "combined_documents": []
        }
        
        for i, file_path in enumerate(downloaded_files):
            await self.send_tool_update("document_analysis", f"Analyzing file {i+1}/{len(downloaded_files)}: {Path(file_path).name}", "executing")
            
            file_analysis = await self._analyze_single_file(file_path)
            document_analysis["file_analysis"].append(file_analysis)
            
            for doc_type in file_analysis.get("detected_types", []):
                document_analysis["detected_document_types"].add(doc_type)
            
            if len(file_analysis.get("detected_types", [])) > 1:
                document_analysis["combined_documents"].append({
                    "filename": file_analysis["filename"],
                    "types": file_analysis["detected_types"],
                    "pages": file_analysis.get("total_pages", 1)
                })
        
        document_analysis["detected_document_types"] = list(document_analysis["detected_document_types"])
        
        await self.send_tool_update("document_analysis", f"Document analysis completed - Found {len(document_analysis['detected_document_types'])} document types", "completed")
        await self.send_analysis_update("document_classification", f"Identified document types: {document_analysis['detected_document_types']}")
        
        return document_analysis
    
    async def _analyze_single_file(self, file_path: str) -> Dict[str, Any]:
        import fitz
        from pathlib import Path
        
        path = Path(file_path)
        file_analysis = {
            "filename": path.name,
            "file_type": path.suffix.lower(),
            "detected_types": [],
            "page_analysis": []
        }
        
        if path.suffix.lower() == '.pdf':
            try:
                pdf_doc = fitz.open(file_path)
                file_analysis["total_pages"] = len(pdf_doc)
                
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]
                    page_text = page.get_text()
                    
                    doc_type = self._classify_page_content(page_text)
                    file_analysis["page_analysis"].append({
                        "page": page_num + 1,
                        "document_type": doc_type,
                        "content_length": len(page_text),
                        "has_tables": self._detect_tabular_content(page_text)
                    })
                    
                    if doc_type != "unknown" and doc_type not in file_analysis["detected_types"]:
                        file_analysis["detected_types"].append(doc_type)
                
                pdf_doc.close()
                
            except Exception:
                file_analysis["detected_types"] = ["unknown"]
                file_analysis["total_pages"] = 1
        
        else:
            file_analysis["detected_types"] = [self._classify_file_by_extension(path.suffix.lower())]
            file_analysis["total_pages"] = 1
        
        return file_analysis
    
    def _classify_page_content(self, content: str) -> str:
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["bordereaux", "claim number", "transaction date", "paid amount", "outstanding"]):
            return "claims_bordereaux"
        elif any(term in content_lower for term in ["statement", "quarterly", "account", "balance", "commission", "total income"]):
            return "cedant_statement"
        elif any(term in content_lower for term in ["notification", "claim notification", "insured name", "date of loss"]):
            return "claim_notification"
        elif any(term in content_lower for term in ["treaty", "reinsured", "commission rate", "profit commission"]):
            return "treaty_contract"
        else:
            return "unknown"
    
    def _classify_file_by_extension(self, extension: str) -> str:
        if extension in ['.xlsx', '.xls']:
            return "claims_bordereaux"
        elif extension in ['.docx', '.doc']:
            return "claim_notification"
        else:
            return "unknown"
    
    def _detect_tabular_content(self, content: str) -> bool:
        lines = content.split('\n')
        tabular_indicators = 0
        
        for line in lines:
            if len(line.split()) > 3 and any(char.isdigit() for char in line):
                tabular_indicators += 1
        
        return tabular_indicators > 3
    
    async def _analyze_email_enhanced(self, email_content, document_analysis):
        await self.send_tool_update("email_analysis", "Performing enhanced email content analysis with AI", "executing")
        
        attachment_info = []
        
        for file_info in document_analysis["file_analysis"]:
            if file_info["detected_types"]:
                for doc_type in file_info["detected_types"]:
                    attachment_info.append(f"{file_info['filename']} - {doc_type}")
            else:
                attachment_info.append(file_info['filename'])
        
        enhanced_body = f"{email_content.body_text}\n\nDETAILED FILE ANALYSIS:\n" + "\n".join(attachment_info)
        
        analysis = self.email_analyzer.analyze_email_content(
            email_content.subject,
            enhanced_body,
            email_content.attachment_filenames
        )
        
        await self.send_tool_update("email_analysis", f"Email analysis completed - Status: {analysis.completion_status}", "completed")
        await self.send_analysis_update("email_completeness", f"Email completeness: {analysis.completion_status}, Documents found: {len(analysis.documents_found)}")
        
        return analysis
    
    async def _create_embeddings(self, downloaded_files: List[str]):
        await self.send_tool_update("vector_embeddings", "Creating document embeddings and building vector store", "executing")
        
        try:
            vector_store = self.embedding_system.build_vector_store(self.vector_store_path)
            await self.send_tool_update("vector_embeddings", f"Vector store created successfully at {self.vector_store_path}", "completed")
            await self.send_analysis_update("embedding_creation", f"Successfully created embeddings for {len(downloaded_files)} documents")
            return vector_store
        except Exception as e:
            await self.send_tool_update("vector_embeddings", f"Vector store creation failed: {str(e)}", "failed")
            raise Exception(f"Failed to create embeddings: {str(e)}")
    
    async def _validate_documents(self, email_analysis, downloaded_files: List[str], document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        await self.send_tool_update("document_validation", "Validating document completeness and integrity", "executing")
        
        detected_types = set(document_analysis.get("detected_document_types", []))
        
        mandatory_types = {"claims_bordereaux", "cedant_statement", "claim_notification"}
        missing_types = mandatory_types - detected_types
        
        completeness_override = len(missing_types) == 0
        
        validation_results = {
            "total_files": len(downloaded_files),
            "document_types_identified": len(email_analysis.documents_found),
            "enhanced_detection": {
                "detected_types": list(detected_types),
                "missing_types": list(missing_types),
                "completeness_override": completeness_override
            },
            "completeness_check": {
                "status": "Complete" if completeness_override else email_analysis.completion_status,
                "all_mandatory_present": completeness_override or email_analysis.all_documents_present,
                "missing_documents": list(missing_types) if missing_types else email_analysis.missing_documents
            },
            "combined_documents": document_analysis.get("combined_documents", []),
            "file_processing_status": "success",
            "embedding_status": "completed"
        }
        
        status = "complete" if completeness_override else "incomplete"
        await self.send_tool_update("document_validation", f"Document validation completed - Status: {status}", "completed")
        
        risk_level = "LOW" if completeness_override else "MEDIUM"
        await self.send_analysis_update("document_validation", f"Document validation: {status}, Missing: {len(missing_types)} types", risk_level)
        
        return validation_results