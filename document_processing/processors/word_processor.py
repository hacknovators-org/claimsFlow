from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredWordDocumentLoader
from .base import BaseDocumentProcessor

class WordProcessor(BaseDocumentProcessor):
    
    def can_process(self, file_path: str) -> bool:
        return self.get_file_extension(file_path) in ['.docx', '.doc']
    
    def extract_content(self, file_path: str) -> List[Document]:
        loader = UnstructuredWordDocumentLoader(file_path)
        documents = loader.load()
        
        for doc in documents:
            doc.metadata.update(self.get_metadata(file_path))
        
        return documents