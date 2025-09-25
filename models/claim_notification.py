from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Decimal, Date, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class ClaimNotification(Base):
    """Claim notification documents"""
    __tablename__ = 'claim_notifications'
    
    id = Column(Integer, primary_key=True)
    claim_number = Column(String(50), unique=True, nullable=False)
    policy_number = Column(String(50), nullable=False)
    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)
    insured_name = Column(String(255), nullable=False)
    
    # Dates
    date_of_loss = Column(Date, nullable=False)
    notification_date = Column(Date)
    policy_period_from = Column(Date)
    policy_period_to = Column(Date)
    
    # Amounts
    sum_insured = Column(Decimal(15, 2))
    gross_claim_amount = Column(Decimal(15, 2))
    ga_retention = Column(Decimal(15, 2))
    surplus_amount = Column(Decimal(15, 2))
    facultative_amount = Column(Decimal(15, 2))
    
    # Classification
    underwriting_year = Column(Integer)
    claim_type = Column(String(100))  # "Cargo Loss Damage", "Water Damage", etc.
    class_code = Column(String(20))  # 8021, 8003, etc.
    contract_type = Column(String(100))
    
    # Status
    status = Column(String(50), default='Outstanding')  # Outstanding, Settled, etc.
    has_recoveries = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    batch = relationship("ProcessingBatch", backref="claim_notifications")
