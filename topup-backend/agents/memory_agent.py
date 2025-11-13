"""
Memory Agent for explain queries using RAG retrieval.

This module provides the Memory Agent that handles "explain" intent queries
by retrieving relevant definitions and schema information from the RAG tool.
"""

from typing import List
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.rag_tool import retrieve


def explain(user_query: str, k: int = 3) -> str:
    """
    Explain a metric, field, or concept using RAG retrieval.
    
    This function handles "explain" intent queries by retrieving relevant
    definitions from the RAG tool and formatting them into a readable response.
    
    Args:
        user_query: User's question about a metric, field, or concept
        k: Number of relevant documents to retrieve (default: 3)
    
    Returns:
        Formatted explanation text combining retrieved definitions
    
    Example:
        >>> explain("What is funding rate?")
        "Funding rate is the percentage of submitted applications that resulted in issued loans..."
        
        >>> explain("What are the different channels?")
        "Channels are the marketing sources through which customers are acquired..."
    """
    # Retrieve relevant documents from RAG tool
    documents = retrieve(user_query, k=k)
    
    # Handle case where no documents are found
    if not documents:
        return (
            "I don't have specific information about that in my knowledge base. "
            "Please try rephrasing your question or ask about metrics like "
            "funding rate, approval rate, channels, grades, or FICO scores."
        )
    
    # Format the response
    response = _format_explanation(documents, user_query)
    
    return response


def _format_explanation(documents: List[str], user_query: str) -> str:
    """
    Format retrieved documents into a readable explanation.
    
    Args:
        documents: List of retrieved document texts
        user_query: Original user query for context
    
    Returns:
        Formatted explanation text
    """
    # If we have a single highly relevant document, return it directly
    if len(documents) == 1:
        return _clean_document_text(documents[0])
    
    # For multiple documents, combine them intelligently
    # Check if documents are Q&A format or definitions
    formatted_docs = []
    
    for doc in documents:
        cleaned = _clean_document_text(doc)
        if cleaned and cleaned not in formatted_docs:
            formatted_docs.append(cleaned)
    
    # If we have multiple distinct pieces of information, combine them
    if len(formatted_docs) == 1:
        return formatted_docs[0]
    elif len(formatted_docs) == 2:
        # Two related pieces of information
        return f"{formatted_docs[0]}\n\n{formatted_docs[1]}"
    else:
        # Three or more pieces - format as a comprehensive answer
        main_answer = formatted_docs[0]
        additional_info = "\n\n".join(formatted_docs[1:])
        return f"{main_answer}\n\n{additional_info}"


def _clean_document_text(text: str) -> str:
    """
    Clean and format a single document text.
    
    Removes Q&A prefixes and cleans up formatting for better readability.
    
    Args:
        text: Raw document text
    
    Returns:
        Cleaned text
    """
    # Remove "Q: ... A: " prefix if present
    if text.startswith("Q:"):
        parts = text.split("A:", 1)
        if len(parts) == 2:
            text = parts[1].strip()
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


# Example usage and testing
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What is funding rate?",
        "What is approval rate?",
        "What are the different channels?",
        "What is FICO?",
        "What's the difference between app submits and app approvals?",
        "What is issuance?",
        "What are grades?",
        "What is MoM and WoW?",
        "How do I calculate conversion rates?",
        "What is variance analysis?"
    ]
    
    print("Memory Agent Test\n" + "=" * 80)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 80)
        response = explain(query)
        print(response)
        print()
