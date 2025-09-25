from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader
from .base import BaseDocumentProcessor

class PDFProcessor(BaseDocumentProcessor):
    
    def can_process(self, file_path: str) -> bool:
        return self.get_file_extension(file_path) == '.pdf'
    
    def extract_content(self, file_path: str) -> List[Document]:
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if not documents or not any(doc.page_content.strip() for doc in documents):
                loader = UnstructuredPDFLoader(file_path)
                documents = loader.load()
            
            for doc in documents:
                doc.metadata.update(self.get_metadata(file_path))
            
            return documents
            
        except Exception:
            loader = UnstructuredPDFLoader(file_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata.update(self.get_metadata(file_path))
            
            return documents