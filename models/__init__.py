from .base import Base
from .treaty_contract import TreatyContract
from .reinsurer import Reinsurer
from .claim_notification import ClaimNotification
from .cash_call import CashCall
from .claim_bordereaux import ClaimBordereaux
from .premium_bordereaux import PremiumBordereaux
from .account_statement import AccountStatement
from .reinsurer_share import ReinsurerShare
from .document_upload import DocumentUpload
from .validation_error import ValidationError

# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def create_database_engine(database_url: str):
    """Create database engine and session factory"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal

__all__ = [
    'Base',
    'TreatyContract',
    'Reinsurer', 
    'ClaimNotification',
    'CashCall',
    'ClaimBordereaux',
    'PremiumBordereaux',
    'AccountStatement',
    'ReinsurerShare',
    'DocumentUpload',
    'ValidationError',
    'create_database_engine'
]