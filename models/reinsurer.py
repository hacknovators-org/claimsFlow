from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Numeric, Date, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class Reinsurer(Base):
    """Reinsurer companies and their shares"""
    __tablename__ = 'reinsurers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100))
    share_percentage = Column(Numeric(5, 4))  # e.g., 0.2000 for 20%
    broker_name = Column(String(255))
    is_statutory = Column(Boolean, default=False)
    treaty_id = Column(Integer, ForeignKey('treaty_contracts.id'))
    
    treaty = relationship("TreatyContract", backref="reinsurers")