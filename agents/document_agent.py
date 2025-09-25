import os
from typing import Dict, Any, List
from pathlib import Path
import shutil
from .base_agent import BaseAgent, AgentStatus
from services.gmail_reader import FocusedGmailConnector
from services.email_analyzer import SimpleEmailAnalyzer
from services.agent import DocumentEmbeddingSystem

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
            
            await self._initialize_services()
            
            await self.send_update("email_connection", "Connecting to Gmail", 10.0)
            email_content = await self._fetch_latest_email(sender_email)
            
            if not email_content:
                raise Exception(f"No emails found from {sender_email}")
            
            await self.send_update("email_analysis", "Analyzing email content", 20.0)
            email_analysis = await self._analyze_email(email_content)
            
            await self.send_update("attachment_download", "Downloading email attachments", 30.0)
            downloaded_files = await self._download_attachments(email_content)
            
            if not downloaded_files:
                raise Exception("No attachments found in email")
            
            await self.send_update("document_processing", "Processing documents and creating embeddings", 50.0)
            vector_store = await self._create_embeddings(downloaded_files)
            
            await self.send_update("data_validation", "Validating document completeness", 80.0)
            validation_results = await self._validate_documents(email_analysis, downloaded_files)
            
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
        email_host = os.getenv("EMAIL_HOST")
        email_password = os.getenv("EMAIL_APP_PASSWORD")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([email_host, email_password, openai_api_key]):
            raise Exception("Missing required environment variables")
        
        self.gmail_connector = FocusedGmailConnector(email_host, email_password)
        self.email_analyzer = SimpleEmailAnalyzer(openai_api_key)
        self.embedding_system = DocumentEmbeddingSystem(openai_api_key, self.download_folder)
        
        os.makedirs(self.download_folder, exist_ok=True)
    
    async def _fetch_latest_email(self, sender_email: str):
        with self.gmail_connector:
            latest_email = self.gmail_connector.read_latest_email_from_sender(sender_email)
            return latest_email
    
    async def _analyze_email(self, email_content):
        analysis = self.email_analyzer.analyze_email_content(
            email_content.subject,
            email_content.body_text,
            email_content.attachment_filenames
        )
        return analysis
    
    async def _download_attachments(self, email_content) -> List[str]:
        if Path(self.download_folder).exists():
            shutil.rmtree(self.download_folder)
        os.makedirs(self.download_folder, exist_ok=True)
        
        with self.gmail_connector:
            downloaded_files = self.gmail_connector.download_attachments(
                email_content, 
                download_folder=self.download_folder
            )
        
        return downloaded_files
    
    async def _create_embeddings(self, downloaded_files: List[str]):
        try:
            vector_store = self.embedding_system.build_vector_store(self.vector_store_path)
            return vector_store
        except Exception as e:
            raise Exception(f"Failed to create embeddings: {str(e)}")
    
    async def _validate_documents(self, email_analysis, downloaded_files: List[str]) -> Dict[str, Any]:
        return {
            "total_files": len(downloaded_files),
            "document_types_identified": len(email_analysis.documents_found),
            "completeness_check": {
                "status": email_analysis.completion_status,
                "all_mandatory_present": email_analysis.all_documents_present,
                "missing_documents": email_analysis.missing_documents
            },
            "file_processing_status": "success",
            "embedding_status": "completed"
        }