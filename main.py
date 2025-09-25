from contextlib import asynccontextmanager
from database import init_database, get_db
from sqlalchemy.orm import Session
from fastapi import FastAPI, Query, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from services.email_analyzer import SimpleEmailAnalyzer
from services.gmail_reader import FocusedGmailConnector
from services.document_processor import DocumentProcessingService
from schemas.emails import EmailAnalysisResponse
from crud.email import analyze_emails_from_sender
from datetime import datetime
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting application...")
    init_database()
    yield

app = FastAPI(
    title="Reinsurance Processing API",
    description="API for processing reinsurance documents and data",
    version="1.0.0",
    lifespan=lifespan
)

class ProcessingResponse(BaseModel):
    batch_id: int
    batch_reference: str
    status: str
    processed_files: int
    total_files: int
    extracted_records: Dict[str, int]
    errors: List[str] = []

@app.get("/")
async def root():
    return {"message": "Reinsurance Processing API is running"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}

@app.get("/check-emails", response_model=List[EmailAnalysisResponse])
async def check_emails(sender_email: str = Query(..., description="Email address of the sender to check")):
    return await analyze_emails_from_sender(sender_email)

@app.post("/process-email-documents", response_model=ProcessingResponse)
async def process_email_documents(
    sender_email: str = Query(..., description="Email address of the sender"),
    db: Session = Depends(get_db)
):
    """
    Download attachments from latest email from sender and process all documents
    """
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
    
    if not EMAIL_HOST or not EMAIL_APP_PASSWORD:
        raise HTTPException(status_code=500, detail="Email configuration missing")
    
    gmail = FocusedGmailConnector(EMAIL_HOST, EMAIL_APP_PASSWORD)
    processor = DocumentProcessingService(db)
    
    try:
        with gmail:
            latest_email = gmail.read_latest_email_from_sender(sender_email)
            
            if not latest_email:
                raise HTTPException(status_code=404, detail=f"No emails found from {sender_email}")
            
            file_paths = gmail.download_attachments(latest_email, download_folder="downloads")
            
            if not file_paths:
                raise HTTPException(status_code=404, detail="No attachments found in email")
            
            email_date = datetime.strptime(latest_email.date, "%a, %d %b %Y %H:%M:%S %z") if latest_email.date else datetime.utcnow()
            
            result = processor.process_email_attachments(
                file_paths=file_paths,
                email_subject=latest_email.subject,
                email_sender=latest_email.sender,
                email_body=latest_email.body_text,
                email_date=email_date
            )
            
            return ProcessingResponse(**result)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch-status/{batch_id}")
async def get_batch_status(batch_id: int, db: Session = Depends(get_db)):
    """Get processing status for a specific batch"""
    processor = DocumentProcessingService(db)
    status = processor.get_batch_status(batch_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status