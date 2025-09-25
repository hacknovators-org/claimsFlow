from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class ValidationError(Base):
    """Track validation errors during processing"""
    __tablename__ = 'validation_errors'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('document_uploads.id'))

    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)

    
    error_type = Column(String(100))  # "date_validation", "amount_mismatch", "cash_call_validation", etc.
    error_message = Column(Text)
    field_name = Column(String(100))
    expected_value = Column(String(255))
    actual_value = Column(String(255))
    
    severity = Column(String(20))  # "error", "warning", "info"
    resolved = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("DocumentUpload", backref="validation_errors")

    batch = relationship("ProcessingBatch", backref="validation_errors")
