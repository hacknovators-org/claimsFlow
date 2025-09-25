from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import UnstructuredExcelLoader
import pandas as pd
from .base import BaseDocumentProcessor

class ExcelProcessor(BaseDocumentProcessor):
    
    def can_process(self, file_path: str) -> bool:
        return self.get_file_extension(file_path) in ['.xlsx', '.xls']
    
    def extract_content(self, file_path: str) -> List[Document]:
        documents = []
        
        try:
            excel_file = pd.ExcelFile(file_path)
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                content = df.to_string(index=False)
                
                metadata = self.get_metadata(file_path)
                metadata['sheet_name'] = sheet_name
                metadata['rows'] = len(df)
                metadata['columns'] = len(df.columns)
                
                doc = Document(
                    page_content=content,
                    metadata=metadata
                )
                documents.append(doc)
            
            return documents
            
        except Exception:
            loader = UnstructuredExcelLoader(file_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata.update(self.get_metadata(file_path))
            
            return documents