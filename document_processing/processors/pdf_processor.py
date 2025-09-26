from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from .base import BaseDocumentProcessor
import fitz

class PDFProcessor(BaseDocumentProcessor):
    
    def can_process(self, file_path: str) -> bool:
        return self.get_file_extension(file_path) == '.pdf'
    
    def extract_content(self, file_path: str) -> List[Document]:
        try:
            documents = []
            pdf_doc = fitz.open(file_path)
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                page_text = page.get_text()
                
                page_metadata = self.get_metadata(file_path)
                page_metadata.update({
                    'page_number': page_num + 1,
                    'total_pages': len(pdf_doc),
                    'document_type': self._classify_page_content(page_text),
                    'page_content_length': len(page_text)
                })
                
                doc = Document(
                    page_content=page_text,
                    metadata=page_metadata
                )
                documents.append(doc)
            
            pdf_doc.close()
            return documents
            
        except Exception:
            try:
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                
                for i, doc in enumerate(documents):
                    doc.metadata.update(self.get_metadata(file_path))
                    doc.metadata.update({
                        'page_number': i + 1,
                        'document_type': self._classify_page_content(doc.page_content)
                    })
                
                return documents
                
            except Exception:
                loader = UnstructuredPDFLoader(file_path)
                documents = loader.load()
                
                for doc in documents:
                    doc.metadata.update(self.get_metadata(file_path))
                    doc.metadata['document_type'] = self._classify_page_content(doc.page_content)
                
                return documents
    
    def _classify_page_content(self, content: str) -> str:
        content_lower = content.lower()
        
        if any(term in content_lower for term in ["bordereaux", "claim number", "transaction date", "paid amount", "outstanding"]):
            return "claims_bordereaux"
        elif any(term in content_lower for term in ["statement", "quarterly", "account", "balance", "commission", "total income"]):
            return "cedant_statement"
        elif any(term in content_lower for term in ["notification", "claim notification", "insured name", "date of loss"]):
            return "claim_notification"
        elif any(term in content_lower for term in ["treaty", "reinsured", "commission rate", "profit commission"]):
            return "treaty_contract"
        else:
            return "unknown"