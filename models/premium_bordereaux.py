from sqlalchemy import Column, ForeignKey, Integer, String, Decimal, Date, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class PremiumBordereaux(Base):
    """Premium bordereaux entries"""
    __tablename__ = 'premium_bordereaux'
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)

    
    # Policy details
    policy_number = Column(String(50), nullable=False)
    endorsement_number = Column(String(50))
    insured_name = Column(String(255), nullable=False)
    dn_number = Column(String(50))  # Debit Note number
    
    # Contract details
    contract_name = Column(String(255))
    underwriting_year = Column(Integer)
    
    # Policy period
    period_from = Column(Date)
    period_to = Column(Date)
    account_date = Column(Date)
    
    # Amounts
    sum_insured = Column(Decimal(15, 2))
    gross_premium = Column(Decimal(15, 2))
    ri_premium = Column(Decimal(15, 2))
    retention_premium = Column(Decimal(15, 2))
    facultative_si = Column(Decimal(15, 2))
    facultative_premium = Column(Decimal(15, 2))
    
    # Percentages
    facultative_percentage = Column(Decimal(5, 4))
    retention_percentage = Column(Decimal(5, 4))
    
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("ProcessingBatch", backref="premium_bordereaux")
