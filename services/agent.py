import os
import pickle
from pathlib import Path
from typing import List, Optional
import faiss
import numpy as np
from langchain.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredExcelLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPDFLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import openai

class DocumentEmbeddingSystem:
    def __init__(self, openai_api_key: str = None, downloads_folder: str = "downloads"):
        if not openai_api_key:
            openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_api_key:
            raise ValueError("OpenAI API key not provided and not found in environment variables")
        
        self.downloads_folder = Path(downloads_folder)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = None
        
        openai.api_key = openai_api_key
        
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}
    
    def load_document(self, file_path: Path) -> List[Document]:
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                try:
                    loader = PyPDFLoader(str(file_path))
                    documents = loader.load()
                    if not documents or all(len(doc.page_content.strip()) < 100 for doc in documents):
                        loader = UnstructuredPDFLoader(str(file_path))
                        documents = loader.load()
                except Exception:
                    loader = UnstructuredPDFLoader(str(file_path))
                    documents = loader.load()
                    
            elif file_extension in ['.docx', '.doc']:
                try:
                    loader = Docx2txtLoader(str(file_path))
                    documents = loader.load()
                    if not documents or all(len(doc.page_content.strip()) < 50 for doc in documents):
                        loader = UnstructuredWordDocumentLoader(str(file_path))
                        documents = loader.load()
                except Exception:
                    loader = UnstructuredWordDocumentLoader(str(file_path))
                    documents = loader.load()
                    
            elif file_extension in ['.xlsx', '.xls']:
                loader = UnstructuredExcelLoader(str(file_path))
                documents = loader.load()
                
            else:
                print(f"Unsupported file type: {file_extension}")
                return []
            
            for doc in documents:
                doc.metadata.update({
                    'source': str(file_path),
                    'filename': file_path.name,
                    'file_type': file_extension
                })
            
            return documents
            
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return []
    
    def process_documents(self) -> List[Document]:
        if not self.downloads_folder.exists():
            raise FileNotFoundError(f"Downloads folder not found: {self.downloads_folder}")
        
        all_documents = []
        processed_files = 0
        
        print(f"Scanning folder: {self.downloads_folder}")
        
        for file_path in self.downloads_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                print(f"Processing: {file_path.name}")
                documents = self.load_document(file_path)
                
                if documents:
                    chunks = self.text_splitter.split_documents(documents)
                    all_documents.extend(chunks)
                    processed_files += 1
                    print(f"  -> Added {len(chunks)} chunks")
                else:
                    print(f"  -> Failed to load document")
        
        print(f"\nProcessed {processed_files} files, created {len(all_documents)} chunks")
        return all_documents
    
    def create_embeddings(self, documents: List[Document]) -> FAISS:
        if not documents:
            raise ValueError("No documents provided for embedding creation")
        
        print("Creating embeddings...")
        vector_store = FAISS.from_documents(documents, self.embeddings)
        print(f"Created embeddings for {len(documents)} document chunks")
        
        return vector_store
    
    def save_vector_store(self, vector_store: FAISS, save_path: str = "faiss_index"):
        vector_store.save_local(save_path)
        print(f"Vector store saved to: {save_path}")
    
    def load_vector_store(self, load_path: str = "faiss_index") -> FAISS:
        vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
        print(f"Vector store loaded from: {load_path}")
        return vector_store
    
    def build_vector_store(self, save_path: str = "faiss_index") -> FAISS:
        documents = self.process_documents()
        
        if not documents:
            raise ValueError("No documents were successfully processed")
        
        vector_store = self.create_embeddings(documents)
        
        self.save_vector_store(vector_store, save_path)
        
        self.vector_store = vector_store
        
        return vector_store
    
    def query_documents(self, query: str, k: int = 5, score_threshold: float = 0.5) -> List[tuple]:
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Run build_vector_store() first or load an existing one.")
        
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        filtered_results = [(doc, score) for doc, score in results if score <= score_threshold]
        
        return filtered_results
    
    def print_query_results(self, query: str, k: int = 5):
        results = self.query_documents(query, k=k)
        
        print(f"\nQuery: '{query}'")
        print(f"Found {len(results)} relevant results:\n")
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"Result {i} (Score: {score:.4f}):")
            print(f"Source: {doc.metadata.get('filename', 'Unknown')}")
            print(f"Content: {doc.page_content[:300]}...")
            print("-" * 80)