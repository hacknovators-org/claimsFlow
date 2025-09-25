# document_processing/pipeline.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from langchain.schema import Document

from .extractors.document_extractor import DocumentExtractor
from .parsers.claim_parser import ClaimParser
from .parsers.premium_parser import PremiumParser
from .parsers.statement_parser import StatementParser
from .parsers.treaty_parser import TreatyParser

from models.processing_batch import ProcessingBatch
from models.claim_notification import ClaimNotification
from models.cash_call import CashCall
from models.claim_bordereaux import ClaimBordereaux
from models.premium_bordereaux import PremiumBordereaux
from models.account_statement import AccountStatement
from models.reinsurer_share import ReinsurerShare
from models.treaty_contract import TreatyContract
from models.reinsurer import Reinsurer
from models.document_upload import DocumentUpload


class DocumentProcessingPipeline:
    
    def __init__(self, db: Session, api_key: str = None):
        self.db = db
        self.extractor = DocumentExtractor()
        self.claim_parser = ClaimParser(api_key)
        self.premium_parser = PremiumParser(api_key)
        self.statement_parser = StatementParser(api_key)
        self.treaty_parser = TreatyParser(api_key)
    
    def process_files(self, file_paths: List[str], batch_id: int) -> Dict[str, Any]:
        results = {
            "processed_files": 0,
            "extracted_records": {},
            "errors": []
        }
        
        batch = self.db.query(ProcessingBatch).filter(ProcessingBatch.id == batch_id).first()
        if not batch:
            results["errors"].append(f"Batch {batch_id} not found")
            return results
        
        for file_path in file_paths:
            try:
                documents = self.extractor.extract_documents(file_path)
                if not documents:
                    continue
                
                doc_upload = self._create_document_upload(file_path, batch_id)
                self.db.add(doc_upload)
                self.db.flush()
                
                document_type = self._identify_document_type(documents)
                extracted_data = self._parse_documents(documents, document_type)
                
                if extracted_data:
                    self._store_extracted_data(extracted_data, batch_id, doc_upload.id)
                    results["extracted_records"][file_path] = len(extracted_data)
                
                results["processed_files"] += 1
                doc_upload.status = "completed"
                
            except Exception as e:
                results["errors"].append(f"Error processing {file_path}: {str(e)}")
                if 'doc_upload' in locals():
                    doc_upload.status = "error"
                    doc_upload.error_message = str(e)
        
        self.db.commit()
        return results
    
    def _identify_document_type(self, documents: List[Document]) -> str:
        content = " ".join([doc.page_content for doc in documents]).lower()
        
        if any(term in content for term in ["claim notification", "claim number", "date of loss", "insured name"]):
            return "claim_notification"
        elif any(term in content for term in ["cash call", "worksheet", "claim_id", "payment partner"]):
            return "cash_call"
        elif any(term in content for term in ["bordereaux", "transaction date", "paid amount", "outstanding"]):
            return "claim_bordereaux"
        elif any(term in content for term in ["premium bordereaux", "policy number", "gross premium"]):
            return "premium_bordereaux"
        elif any(term in content for term in ["account statement", "quarterly", "commission", "balance"]):
            return "account_statement"
        elif any(term in content for term in ["treaty", "reinsured", "commission rate", "profit commission"]):
            return "treaty_contract"
        else:
            return "unknown"
    
    def _parse_documents(self, documents: List[Document], document_type: str) -> List[Any]:
        if document_type == "claim_notification":
            return self.claim_parser.parse_claim_notification(documents)
        elif document_type == "cash_call":
            return self.claim_parser.parse_cash_calls(documents)
        elif document_type == "claim_bordereaux":
            return self.claim_parser.parse_claim_bordereaux(documents)
        elif document_type == "premium_bordereaux":
            return self.premium_parser.parse_premium_bordereaux(documents)
        elif document_type == "account_statement":
            return self.statement_parser.parse_account_statement(documents)
        elif document_type == "treaty_contract":
            return self.treaty_parser.parse_treaty_contract(documents)
        else:
            return []
    
    def _store_extracted_data(self, data: List[Any], batch_id: int, doc_upload_id: int):
        for record in data:
            if hasattr(record, 'claim_number'):
                self._store_claim_notification(record, batch_id)
            elif hasattr(record, 'claim_id'):
                self._store_cash_call(record, batch_id)
            elif hasattr(record, 'transaction_date'):
                self._store_claim_bordereaux(record, batch_id)
            elif hasattr(record, 'policy_number'):
                self._store_premium_bordereaux(record, batch_id)
            elif hasattr(record, 'account_period'):
                self._store_account_statement(record, batch_id)
            elif hasattr(record, 'treaty_name'):
                self._store_treaty_contract(record, batch_id)
    
    def _store_claim_notification(self, record, batch_id: int):
        claim = ClaimNotification(
            claim_number=record.claim_number,
            policy_number=record.policy_number,
            insured_name=record.insured_name,
            date_of_loss=record.date_of_loss,
            notification_date=record.notification_date,
            sum_insured=record.sum_insured,
            gross_claim_amount=record.gross_claim_amount,
            claim_type=record.claim_type,
            class_code=record.class_code,
            batch_id=batch_id
        )
        self.db.add(claim)
    
    def _store_cash_call(self, record, batch_id: int):
        cash_call = CashCall(
            claim_id=record.claim_id,
            worksheet_id=record.worksheet_id,
            business_id=record.business_id,
            claim_name=record.claim_name,
            date_of_loss=record.date_of_loss,
            currency_code=record.currency_code,
            amount_original=record.amount_original,
            payment_partner_name=record.payment_partner_name,
            batch_id=batch_id
        )
        self.db.add(cash_call)
    
    def _store_claim_bordereaux(self, record, batch_id: int):
        claim_notification = self.db.query(ClaimNotification).filter(
            ClaimNotification.claim_number == record.claim_number
        ).first()
        
        bordereaux = ClaimBordereaux(
            notification_id=claim_notification.id if claim_notification else None,
            transaction_date=record.transaction_date,
            transaction_type=record.transaction_type,
            paid_amount=record.paid_amount,
            outstanding_amount=record.outstanding_amount,
            batch_id=batch_id
        )
        self.db.add(bordereaux)
    
    def _store_premium_bordereaux(self, record, batch_id: int):
        premium = PremiumBordereaux(
            policy_number=record.policy_number,
            insured_name=record.insured_name,
            period_from=record.period_from,
            period_to=record.period_to,
            sum_insured=record.sum_insured,
            gross_premium=record.gross_premium,
            ri_premium=record.ri_premium,
            retention_premium=record.retention_premium,
            underwriting_year=record.underwriting_year,
            batch_id=batch_id
        )
        self.db.add(premium)
    
    def _store_account_statement(self, record, batch_id: int):
        statement = AccountStatement(
            account_period=record.account_period,
            underwriting_year=record.underwriting_year,
            currency=record.currency,
            cargo_premium=record.cargo_premium,
            hull_premium=record.hull_premium,
            total_income=record.total_income,
            commission_rate=record.commission_rate,
            commission_amount=record.commission_amount,
            claims_paid=record.claims_paid,
            outstanding_claims=record.outstanding_claims,
            balance=record.balance,
            batch_id=batch_id
        )
        self.db.add(statement)
    
    def _store_treaty_contract(self, record, batch_id: int):
        treaty = TreatyContract(
            treaty_name=record.treaty_name,
            reinsured_name=record.reinsured_name,
            treaty_type=record.treaty_type,
            underwriting_year=record.underwriting_year,
            period_from=record.period_from,
            period_to=record.period_to,
            currency=record.currency,
            commission_rate=record.commission_rate,
            profit_commission_rate=record.profit_commission_rate
        )
        self.db.add(treaty)
    
    def _create_document_upload(self, file_path: str, batch_id: int) -> DocumentUpload:
        from pathlib import Path
        path = Path(file_path)
        
        return DocumentUpload(
            batch_id=batch_id,
            filename=path.name,
            file_path=str(path),
            file_type=path.suffix.lower(),
            status="processing"
        )