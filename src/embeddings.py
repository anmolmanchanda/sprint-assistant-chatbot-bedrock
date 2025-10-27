"""
Embeddings module for loading PDFs and creating vector store.
"""
import os
import boto3
import chromadb
from chromadb.config import Settings
from PyPDF2 import PdfReader
from typing import List, Dict


class EmbeddingsManager:
    def __init__(self, aws_region="us-east-1"):
        """Initialize Bedrock client and Chroma DB."""
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws_region
        )
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "sprint_reports"
        
    def load_pdfs_from_folder(self, folder_path: str) -> List[Dict]:
        """Load all PDFs from a folder and extract text."""
        documents = []
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
        
        if not pdf_files:
            raise ValueError(f"No PDF files found in {folder_path}")
        
        print(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            file_path = os.path.join(folder_path, pdf_file)
            print(f"Loading {pdf_file}...")
            
            try:
                reader = PdfReader(file_path)
                text = ""
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                
                # Split into chunks (simple approach)
                chunks = self._split_text(text)
                
                for i, chunk in enumerate(chunks):
                    documents.append({
                        "id": f"{pdf_file}_{i}",
                        "text": chunk,
                        "metadata": {
                            "source": pdf_file,
                            "chunk_id": i
                        }
                    })
                    
            except Exception as e:
                print(f"Error loading {pdf_file}: {e}")
                continue
        
        print(f"Loaded {len(documents)} document chunks")
        return documents
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into chunks with overlap."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from Bedrock Titan."""
        embeddings = []
        
        for text in texts:
            try:
                response = self.bedrock.invoke_model(
                    modelId="amazon.titan-embed-text-v1",
                    body='{"inputText": "' + text.replace('"', '\\"').replace('\n', ' ')[:8000] + '"}'
                )
                
                import json
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
                
            except Exception as e:
                print(f"Error getting embedding: {e}")
                embeddings.append([0.0] * 1536)  # Default embedding
        
        return embeddings
    
    def create_vector_store(self, documents: List[Dict]):
        """Create or update vector store with documents."""
        print("Creating vector store...")
        
        # Get or create collection
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
        except:
            pass
        
        collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "Sprint report embeddings"}
        )
        
        # Prepare data
        texts = [doc["text"] for doc in documents]
        ids = [doc["id"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        # Get embeddings in batches
        print("Generating embeddings...")
        batch_size = 5
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.get_embeddings(batch)
            all_embeddings.extend(batch_embeddings)
            print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} chunks")
        
        # Add to collection
        collection.add(
            embeddings=all_embeddings,
            documents=texts,
            ids=ids,
            metadatas=metadatas
        )
        
        print(f"Vector store created with {len(documents)} chunks")
        return collection


def setup_vector_store(data_folder: str = "./data"):
    """Main function to set up the vector store."""
    manager = EmbeddingsManager()
    documents = manager.load_pdfs_from_folder(data_folder)
    collection = manager.create_vector_store(documents)
    return collection


if __name__ == "__main__":
    # Run this to create the vector store
    setup_vector_store()
