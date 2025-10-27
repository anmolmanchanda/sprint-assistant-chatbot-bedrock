"""
Retrieval module for querying the vector store.
"""
import boto3
import chromadb
import json
from typing import List, Dict


class VectorRetriever:
    def __init__(self, aws_region="us-east-1"):
        """Initialize retriever with Bedrock and Chroma."""
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws_region
        )
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "sprint_reports"
        
        try:
            self.collection = self.chroma_client.get_collection(name=self.collection_name)
        except:
            raise ValueError("Vector store not found. Please run embeddings.py first.")
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for a query."""
        try:
            response = self.bedrock.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body='{"inputText": "' + query.replace('"', '\\"')[:8000] + '"}'
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['embedding']
            
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            return None
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search for relevant documents."""
        query_embedding = self.get_query_embedding(query)
        
        if query_embedding is None:
            return []
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'text': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    
    def format_context(self, documents: List[Dict]) -> str:
        """Format retrieved documents as context."""
        if not documents:
            return "No relevant documents found."
        
        context = ""
        for i, doc in enumerate(documents, 1):
            source = doc['metadata'].get('source', 'Unknown')
            context += f"\n[Document {i} - {source}]\n{doc['text']}\n"
        
        return context


if __name__ == "__main__":
    # Test retrieval
    retriever = VectorRetriever()
    results = retriever.search("What were the key accomplishments?")
    print(f"Found {len(results)} results")
    for doc in results:
        print(f"- {doc['metadata'].get('source', 'Unknown')}")
