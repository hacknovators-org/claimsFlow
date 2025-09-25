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
from dotenv import load_dotenv

load_dotenv('../.env')
import os
OPEANAI_API_KEY = os.getenv('OPENAI_API_KEY')

class DocumentEmbeddingSystem:
    def __init__(self, openai_api_key: str, downloads_folder: str = "downloads"):
        """
        Initialize the document embedding system.
        
        Args:
            openai_api_key: Your OpenAI API key
            downloads_folder: Path to your downloads folder
        """
        self.downloads_folder = Path(downloads_folder)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.vector_store = None
        
        # Set OpenAI API key
        openai.api_key = openai_api_key
        
        # Supported file extensions
        self.supported_extensions = {'.pdf', '.docx', '.doc', '.xlsx', '.xls'}
    
    def load_document(self, file_path: Path) -> List[Document]:
        """
        Load a document based on its file extension.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of Document objects
        """
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                # Try structured loader first, fallback to unstructured
                try:
                    loader = PyPDFLoader(str(file_path))
                    documents = loader.load()
                    # If structured loader gives poor results, use unstructured
                    if not documents or all(len(doc.page_content.strip()) < 100 for doc in documents):
                        loader = UnstructuredPDFLoader(str(file_path))
                        documents = loader.load()
                except Exception:
                    loader = UnstructuredPDFLoader(str(file_path))
                    documents = loader.load()
                    
            elif file_extension in ['.docx', '.doc']:
                # Try structured loader first, fallback to unstructured
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
            
            # Add metadata
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
        """
        Process all supported documents in the downloads folder.
        
        Returns:
            List of processed document chunks
        """
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
                    # Split documents into chunks
                    chunks = self.text_splitter.split_documents(documents)
                    all_documents.extend(chunks)
                    processed_files += 1
                    print(f"  -> Added {len(chunks)} chunks")
                else:
                    print(f"  -> Failed to load document")
        
        print(f"\nProcessed {processed_files} files, created {len(all_documents)} chunks")
        return all_documents
    
    def create_embeddings(self, documents: List[Document]) -> FAISS:
        """
        Create embeddings and build FAISS vector store.
        
        Args:
            documents: List of document chunks
            
        Returns:
            FAISS vector store
        """
        if not documents:
            raise ValueError("No documents provided for embedding creation")
        
        print("Creating embeddings...")
        vector_store = FAISS.from_documents(documents, self.embeddings)
        print(f"Created embeddings for {len(documents)} document chunks")
        
        return vector_store
    
    def save_vector_store(self, vector_store: FAISS, save_path: str = "faiss_index"):
        """
        Save the FAISS vector store to disk.
        
        Args:
            vector_store: FAISS vector store to save
            save_path: Path where to save the vector store
        """
        vector_store.save_local(save_path)
        print(f"Vector store saved to: {save_path}")
    
    def load_vector_store(self, load_path: str = "faiss_index") -> FAISS:
        """
        Load a FAISS vector store from disk.
        
        Args:
            load_path: Path to load the vector store from
            
        Returns:
            Loaded FAISS vector store
        """
        vector_store = FAISS.load_local(load_path, self.embeddings)
        print(f"Vector store loaded from: {load_path}")
        return vector_store
    
    def build_vector_store(self, save_path: str = "faiss_index") -> FAISS:
        """
        Complete workflow: process documents, create embeddings, and save.
        
        Args:
            save_path: Path to save the vector store
            
        Returns:
            FAISS vector store
        """
        # Process documents
        documents = self.process_documents()
        
        if not documents:
            raise ValueError("No documents were successfully processed")
        
        # Create embeddings
        vector_store = self.create_embeddings(documents)
        
        # Save vector store
        self.save_vector_store(vector_store, save_path)
        
        # Store reference
        self.vector_store = vector_store
        
        return vector_store
    
    def query_documents(self, query: str, k: int = 5, score_threshold: float = 0.5) -> List[tuple]:
        """
        Query the vector store for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of tuples (document, score)
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Run build_vector_store() first or load an existing one.")
        
        # Perform similarity search with scores
        results = self.vector_store.similarity_search_with_score(query, k=k)
        
        # Filter by score threshold
        filtered_results = [(doc, score) for doc, score in results if score <= score_threshold]
        
        return filtered_results
    
    def print_query_results(self, query: str, k: int = 5):
        """
        Query and print formatted results.
        
        Args:
            query: Search query
            k: Number of results to return
        """
        results = self.query_documents(query, k=k)
        
        print(f"\nQuery: '{query}'")
        print(f"Found {len(results)} relevant results:\n")
        
        for i, (doc, score) in enumerate(results, 1):
            print(f"Result {i} (Score: {score:.4f}):")
            print(f"Source: {doc.metadata.get('filename', 'Unknown')}")
            print(f"Content: {doc.page_content[:300]}...")
            print("-" * 80)

# Example usage
def main():
    # Initialize the system (replace with your OpenAI API key)
    API_KEY = OPEANAI_API_KEY
    embedding_system = DocumentEmbeddingSystem(
        openai_api_key=API_KEY,
        downloads_folder="downloads"  # Adjust path as needed
    )
    
    try:
        # Build the vector store (this will process all documents and create embeddings)
        print("Building vector store...")
        vector_store = embedding_system.build_vector_store("my_faiss_index")
        
        # Example queries
        queries = [
            "financial data and revenue",
            "project timeline and milestones",
            "risk assessment",
            "budget allocation"
        ]
        
        print("\n" + "="*80)
        print("TESTING QUERIES")
        print("="*80)
        
        for query in queries:
            embedding_system.print_query_results(query, k=3)
        
    except Exception as e:
        print(f"Error: {str(e)}")

    # To load an existing vector store later:
    # embedding_system.vector_store = embedding_system.load_vector_store("my_faiss_index")
    # embedding_system.print_query_results("your query here")

if __name__ == "__main__":
    main()