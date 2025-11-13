"""
Demo of RAG Tool with real ChromaDB and OpenAI embeddings.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.rag_tool import retrieve


def demo_rag_queries():
    """Demonstrate RAG tool with various queries."""
    print("=" * 70)
    print("RAG Tool Demo - Real ChromaDB + OpenAI Embeddings")
    print("=" * 70)
    print()
    
    queries = [
        ("What is funding rate?", 2),
        ("Explain approval rate", 2),
        ("What are the different channels?", 3),
        ("What is FICO?", 2),
        ("How do I calculate conversion rates?", 2),
        ("What's the difference between app submits and approvals?", 2),
    ]
    
    for i, (query, k) in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 70)
        
        results = retrieve(query, k=k)
        
        for j, result in enumerate(results, 1):
            # Clean up Q&A format for display
            if result.startswith("Q:"):
                parts = result.split("A:", 1)
                if len(parts) == 2:
                    result = parts[1].strip()
            
            print(f"\nResult {j}:")
            # Truncate long results
            if len(result) > 300:
                print(f"{result[:300]}...")
            else:
                print(result)
        
        print()
        print("=" * 70)
        print()


if __name__ == "__main__":
    try:
        demo_rag_queries()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
