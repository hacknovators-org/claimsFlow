from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.schema import Document
from pathlib import Path

class BaseDocumentProcessor(ABC):
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        pass
    
    @abstractmethod
    def extract_content(self, file_path: str) -> List[Document]:
        pass
    
    def get_file_extension(self, file_path: str) -> str:
        return Path(file_path).suffix.lower()
    
    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        return {
            "filename": path.name,
            "file_type": path.suffix.lower(),
            "file_size": path.stat().st_size,
            "source": str(path)
        }