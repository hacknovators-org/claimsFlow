from typing import List, Optional
from langchain.schema import Document
from ..processors.pdf_processor import PDFProcessor
from ..processors.excel_processor import ExcelProcessor
from ..processors.csv_processor import CSVProcessor
from ..processors.word_processor import WordProcessor
from ..processors.base import BaseDocumentProcessor

class DocumentExtractor:
    
    def __init__(self):
        self.processors: List[BaseDocumentProcessor] = [
            PDFProcessor(),
            ExcelProcessor(),
            CSVProcessor(),
            WordProcessor()
        ]
    
    def get_processor(self, file_path: str) -> Optional[BaseDocumentProcessor]:
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None
    
    def extract_documents(self, file_path: str) -> List[Document]:
        processor = self.get_processor(file_path)
        if processor:
            return processor.extract_content(file_path)
        return []