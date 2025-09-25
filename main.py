from contextlib import asynccontextmanager
from database import init_database, get_db
from sqlalchemy.orm import Session
from fastapi import FastAPI, Query,Depends
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from services.email_analyzer import SimpleEmailAnalyzer
from services.gmail_reader import FocusedGmailConnector  # import your Gmail connector class
from schemas.emails import EmailAnalysisResponse
from crud.email import analyze_emails_from_sender
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

