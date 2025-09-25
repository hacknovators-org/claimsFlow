from sqlalchemy import Column, Integer, String, Decimal, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class ClaimBordereaux(Base):
    """Claims bordereaux entries"""
    __tablename__ = 'claim_bordereaux'
    
    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey('claim_notifications.id'))
    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)

    
    # Transaction details
    transaction_date = Column(Date)
    transaction_type = Column(String(20))  # S = Settlement, C = Case, etc.
    
    # Amounts
    paid_amount = Column(Decimal(15, 2))
    outstanding_amount = Column(Decimal(15, 2))
    
    # References
    approval_date = Column(Date)
    intermediary_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    claim = relationship("ClaimNotification", backref="bordereaux_entries")

    batch = relationship("ProcessingBatch", backref="claim_bordereaux")