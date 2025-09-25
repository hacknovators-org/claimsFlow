from sqlalchemy import Column, Integer, String, Decimal, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class ReinsurerShare(Base):
    """Individual reinsurer shares in account statements"""
    __tablename__ = 'reinsurer_shares'
    
    id = Column(Integer, primary_key=True)
    account_statement_id = Column(Integer, ForeignKey('account_statements.id'))
    reinsurer_name = Column(String(255), nullable=False)
    broker_name = Column(String(255))
    
    share_amount = Column(Decimal(15, 2))
    share_percentage = Column(Decimal(5, 4))
    is_statutory = Column(Boolean, default=False)
    
    statement = relationship("AccountStatement", backref="reinsurer_shares")