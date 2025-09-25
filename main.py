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

@app.get("/")
async def root():
    return {"message": "Reinsurance Processing API is running"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy", "database": "connected"}





@app.get("/check-emails", response_model=List[EmailAnalysisResponse])
async def check_emails(sender_email: str = Query(..., description="Email address of the sender to check")):
    return await analyze_emails_from_sender(sender_email)

