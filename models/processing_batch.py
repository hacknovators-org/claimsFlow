from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Decimal
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class ProcessingBatch(Base):
    """Core model to track each email processing batch"""
    __tablename__ = 'processing_batches'
    
    id = Column(Integer, primary_key=True)
    
    email_subject = Column(String(500))
    email_sender = Column(String(255), nullable=False)
    email_received_date = Column(DateTime, nullable=False)
    email_body = Column(Text)
    
    batch_reference = Column(String(50), unique=True, nullable=False) 
    accounting_quarter = Column(String(20))  # e.g., "Q2 2024"
    underwriting_year = Column(Integer)
    cedant_name = Column(String(255))
    
    status = Column(String(50), default='received')
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    total_documents = Column(Integer, default=0)
    processed_documents = Column(Integer, default=0)
    validation_errors_count = Column(Integer, default=0)
    validation_warnings_count = Column(Integer, default=0)
    
    total_claims_amount = Column(Decimal(15, 2))
    total_premiums_amount = Column(Decimal(15, 2))
    claims_count = Column(Integer, default=0)
    premiums_count = Column(Integer, default=0)
    
    # Flags
    requires_supervisor_review = Column(Boolean, default=False)
    has_exclusion_violations = Column(Boolean, default=False)
    has_amount_mismatches = Column(Boolean, default=False)
    auto_approved = Column(Boolean, default=False)
    
    processing_notes = Column(Text)
    supervisor_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_by = Column(String(100))
   
    
    @property
    def processing_duration(self):
        """Calculate processing duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_processing_complete(self):
        """Check if processing is complete"""
        return self.status in ['completed', 'failed']
    
    @property
    def success_rate(self):
        """Calculate processing success rate"""
        if self.total_documents == 0:
            return 0
        return (self.processed_documents / self.total_documents) * 100
    
    @property
    def has_critical_errors(self):
        """Check if batch has critical validation errors"""
        return self.validation_errors_count > 0 or self.status == 'failed'
    
    def generate_batch_reference(self):
        """Generate unique batch reference"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"BATCH_{timestamp}_{self.id or 'NEW'}"