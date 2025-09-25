from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class DocumentUpload(Base):
    """Track uploaded documents for processing"""
    __tablename__ = 'document_uploads'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(50))  # "treaty", "bordereaux", "statement", "cash_calls"
    
    # Processing status
    status = Column(String(50), default='uploaded')  # uploaded, processing, completed, error
    processed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Extracted data counts
    claims_extracted = Column(Integer, default=0)
    premiums_extracted = Column(Integer, default=0)
    cash_calls_extracted = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    batch = relationship("ProcessingBatch", backref="document_uploads")
