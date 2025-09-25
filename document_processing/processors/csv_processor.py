from typing import List
from langchain.schema import Document
from langchain_community.document_loaders import CSVLoader
import pandas as pd
from .base import BaseDocumentProcessor

class CSVProcessor(BaseDocumentProcessor):
    
    def can_process(self, file_path: str) -> bool:
        return self.get_file_extension(file_path) == '.csv'
    
    def extract_content(self, file_path: str) -> List[Document]:
        try:
            df = pd.read_csv(file_path)
            content = df.to_string(index=False)
            
            metadata = self.get_metadata(file_path)
            metadata['rows'] = len(df)
            metadata['columns'] = len(df.columns)
            metadata['headers'] = list(df.columns)
            
            return [Document(page_content=content, metadata=metadata)]
            
        except Exception:
            loader = CSVLoader(file_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata.update(self.get_metadata(file_path))
            
            return documents