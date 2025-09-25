from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from document_processing import DocumentProcessingPipeline
from models.processing_batch import ProcessingBatch
from models.document_upload import DocumentUpload
import os


class DocumentProcessingService:
    
    def __init__(self, db: Session, api_key: str = None):
        self.db = db
        self.pipeline = DocumentProcessingPipeline(db, api_key)
    
    def process_email_attachments(
        self, 
        file_paths: List[str], 
        email_subject: str,
        email_sender: str,
        email_body: str,
        email_date: datetime
    ) -> Dict[str, Any]:
        
        batch = self._create_processing_batch(
            email_subject, email_sender, email_body, email_date
        )
        
        batch.status = "processing"
        batch.started_at = datetime.utcnow()
        batch.total_documents = len(file_paths)
        self.db.commit()
        
        try:
            results = self.pipeline.process_files(file_paths, batch.id)
            
            batch.processed_documents = results["processed_files"]
            batch.status = "completed" if not results["errors"] else "completed_with_errors"
            batch.completed_at = datetime.utcnow()
            
            if results["errors"]:
                batch.processing_notes = "; ".join(results["errors"])
            
            self.db.commit()
            
            return {
                "batch_id": batch.id,
                "batch_reference": batch.batch_reference,
                "status": batch.status,
                "processed_files": results["processed_files"],
                "total_files": len(file_paths),
                "extracted_records": results["extracted_records"],
                "errors": results["errors"]
            }
            
        except Exception as e:
            batch.status = "failed"
            batch.processing_notes = str(e)
            batch.completed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "batch_id": batch.id,
                "status": "failed",
                "error": str(e)
            }
    
    def _create_processing_batch(
        self,
        email_subject: str,
        email_sender: str, 
        email_body: str,
        email_date: datetime
    ) -> ProcessingBatch:
        
        batch = ProcessingBatch(
            email_subject=email_subject,
            email_sender=email_sender,
            email_body=email_body,
            email_received_date=email_date,
            status="received"
        )
        
        self.db.add(batch)
        self.db.flush()
        
        batch.batch_reference = batch.generate_batch_reference()
        
        return batch
    
    def get_batch_status(self, batch_id: int) -> Dict[str, Any]:
        batch = self.db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
        
        if not batch:
            return {"error": "Batch not found"}
        
        documents = self.db.query(DocumentUpload).filter(
            DocumentUpload.batch_id == batch_id
        ).all()
        
        return {
            "batch_id": batch.id,
            "batch_reference": batch.batch_reference,
            "status": batch.status,
            "email_sender": batch.email_sender,
            "email_subject": batch.email_subject,
            "total_documents": batch.total_documents,
            "processed_documents": batch.processed_documents,
            "processing_duration": batch.processing_duration,
            "success_rate": batch.success_rate,
            "documents": [
                {
                    "filename": doc.filename,
                    "file_type": doc.file_type,
                    "status": doc.status,
                    "claims_extracted": doc.claims_extracted,
                    "premiums_extracted": doc.premiums_extracted,
                    "error_message": doc.error_message
                }
                for doc in documents
            ]
        }