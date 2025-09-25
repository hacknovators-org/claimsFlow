from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from .base import Base
from datetime import datetime

class TreatyContract(Base):
    """Treaty contract master data"""
    __tablename__ = 'treaty_contracts'
    
    id = Column(Integer, primary_key=True)
    treaty_name = Column(String(255), nullable=False)
    reinsured_name = Column(String(255), nullable=False)
    treaty_type = Column(String(100))  # e.g., "Marine Hull and Cargo Surplus"
    underwriting_year = Column(Integer, nullable=False)
    period_from = Column(Date, nullable=False)
    period_to = Column(Date, nullable=False)
    currency = Column(String(10))  # KES, TZS, UGX, USD
    commission_rate = Column(Numeric(5, 4))  # e.g., 0.2750 for 27.5%
    profit_commission_rate = Column(Numeric(5, 4))  # e.g., 0.4250 for 42.5%
    
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)