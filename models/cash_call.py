from sqlalchemy import Column, Integer, String, Decimal, Date, DateTime, Text
from .base import Base
from datetime import datetime

class CashCall(Base):
    """Cash calls processed for claim validation"""
    __tablename__ = 'cash_calls'
    
    id = Column(Integer, primary_key=True)
    
    # Core identifiers
    claim_id = Column(String(20), nullable=False, index=True)  # e.g., "0000054954"
    worksheet_id = Column(String(20), nullable=False)  # e.g., "CW71051"
    business_id = Column(String(20), nullable=False)  # e.g., "PTTY830"
    
    # Business details
    business_title = Column(String(255))  # e.g., "MARINE CARGO SURPLUS"
    main_class_of_business = Column(String(100))  # e.g., "Marine"
    claim_name = Column(String(500))  # e.g., "M/S IRCON INTERNATIONAL LTD"
    
    # Partner information
    payment_partner_name = Column(String(255))  # Broker name
    responsible_partner_name = Column(String(255))  # Insurance company
    responsible_partner_country = Column(String(100))
    
    # Claim details
    date_of_loss = Column(Date, nullable=False)
    currency_code = Column(String(10), nullable=False)  # ETB, USD, MUR, TZS
    claim_fgu = Column(Integer, default=0)
    
    # Financial amounts
    amount_original = Column(Decimal(15, 2))  # Original amount in claim currency
    functional_amount = Column(Decimal(15, 2))  # Converted to functional currency
    
    # Status and processing
    settlement_indicator = Column(String(20))  # "Settled", "Unsettled"
    ws_registered_by_id = Column(String(50))  # User who registered
    date_of_booking = Column(Date)
    worksheet_notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Helper properties
    @property
    def is_settled(self):
        return self.settlement_indicator == "Settled"
    
    @property
    def absolute_original_amount(self):
        return abs(self.amount_original) if self.amount_original else 0
    
    @property
    def absolute_functional_amount(self):
        return abs(self.functional_amount) if self.functional_amount else 0