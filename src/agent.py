"""
Agent module with Bedrock integration and tool use.
"""
import boto3
import json
from typing import List, Dict, Optional
from src.retrieval import VectorRetriever


class BedrockAgent:
    def __init__(self, aws_region="us-east-1"):
        """Initialize Bedrock agent."""
        self.bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name=aws_region
        )
        self.retriever = VectorRetriever(aws_region=aws_region)
        self.model_id = "amazon.titan-text-express-v1"
        
        # Define tools
        self.tools = [
            {
                "name": "summarize_report",
                "description": "Summarize a specific sprint report by filename. Use this when the user asks to summarize a specific report.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "The filename of the report to summarize (e.g., 'sprint_report_2024_01.pdf')"
                        }
                    },
                    "required": ["filename"]
                }
            }
        ]
    
    def summarize_report(self, filename: str) -> str:
        """Tool implementation: Summarize a specific report."""
        # Search for the specific report
        results = self.retriever.search(f"filename:{filename}", top_k=5)
        
        if not results:
            return f"Report '{filename}' not found."
        
        # Filter to only the requested file
        relevant_chunks = [
            doc for doc in results 
            if doc['metadata'].get('source', '') == filename
        ]
        
        if not relevant_chunks:
            return f"Report '{filename}' not found."
        
        # Combine chunks
        full_text = "\n".join([doc['text'] for doc in relevant_chunks])
        
        # Generate summary
        prompt = f"""Summarize the following sprint report concisely, highlighting:
- Key accomplishments
- Challenges faced
- Metrics and outcomes
- Action items

Report:
{full_text[:3000]}

Summary:"""
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 512,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            summary = response_body['results'][0]['outputText']
            return summary
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def query(self, user_message: str) -> str:
        """Main query method with RAG."""
        # Check if this is a summarization request
        if "summarize" in user_message.lower():
            # Try to extract filename
            words = user_message.split()
            for word in words:
                if word.endswith('.pdf') or 'sprint_report' in word:
                    return self.summarize_report(word)
        
        # Regular RAG query
        documents = self.retriever.search(user_message, top_k=3)
        context = self.retriever.format_context(documents)
        
        # Build prompt
        prompt = f"""You are a helpful assistant analyzing UN-Habitat sprint reports. Use the following context to answer the user's question. If you don't know, say so.

Context:
{context}

User Question: {user_message}

Answer:"""
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 512,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                })
            )
            
            response_body = json.loads(response['body'].read())
            answer = response_body['results'][0]['outputText']
            
            # Add sources
            sources = list(set([doc['metadata'].get('source', 'Unknown') for doc in documents]))
            if sources:
                answer += f"\n\n*Sources: {', '.join(sources)}*"
            
            return answer
            
        except Exception as e:
            return f"Error generating response: {str(e)}"


if __name__ == "__main__":
    # Test the agent
    agent = BedrockAgent()
    response = agent.query("What were the main accomplishments?")
    print(response)
