from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Date, DateTime
from .base import Base
from datetime import datetime
from sqlalchemy.orm import relationship


class AccountStatement(Base):
    """Quarterly account statements"""
    __tablename__ = 'account_statements'
    
    id = Column(Integer, primary_key=True)

    batch_id = Column(Integer, ForeignKey('processing_batches.id'), nullable=True)

    
    # Statement details
    currency = Column(String(10), nullable=False)
    account_period = Column(String(20))  # "Second Quarter 2024"
    underwriting_year = Column(Integer)
    statement_date = Column(Date)
    
    # Premium income
    cargo_premium = Column(Numeric(15, 2), default=0)
    hull_premium = Column(Numeric(15, 2), default=0)
    ri_premium = Column(Numeric(15, 2), default=0)
    total_income = Column(Numeric(15, 2))
    
    # Commissions and taxes
    commission_rate = Column(Numeric(5, 4))
    commission_amount = Column(Numeric(15, 2))
    premium_tax_rate = Column(Numeric(5, 4))
    premium_tax_amount = Column(Numeric(15, 2))
    
    # Claims
    claims_paid = Column(Numeric(15, 2), default=0)
    outstanding_claims = Column(Numeric(15, 2), default=0)
    
    # Totals
    total_outgo = Column(Numeric(15, 2))
    balance = Column(Numeric(15, 2))
    
    # Status
    prepared_by = Column(String(100))
    confirmed_by = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("ProcessingBatch", backref="account_statements")
