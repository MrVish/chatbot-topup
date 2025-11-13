"""
Tests for RAG Tool functionality.
"""

import os
import tempfile
import shutil
from tools.rag_tool import RAGTool, get_rag_tool, retrieve


def test_rag_tool_initialization():
    """Test RAG tool initialization with persistent storage."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool(persist_directory=temp_dir)
        
        # Verify collection was created
        assert rag_tool.collection is not None
        assert rag_tool.collection.name == "topup_glossary"
        
        # Verify documents were indexed
        count = rag_tool.collection.count()
        assert count > 0, f"Expected documents to be indexed, but count is {count}"
        print(f"✓ RAG tool initialized with {count} documents")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_retrieve_kpi_definition():
    """Test retrieving KPI definitions."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool(persist_directory=temp_dir)
        
        # Test funding rate query
        results = rag_tool.retrieve("What is funding rate?", k=3)
        
        assert len(results) > 0, "Expected results for funding rate query"
        assert any("funding rate" in result.lower() for result in results), \
            "Expected at least one result to mention funding rate"
        
        print(f"✓ Retrieved {len(results)} results for 'What is funding rate?'")
        print(f"  Top result: {results[0][:100]}...")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_retrieve_schema_info():
    """Test retrieving schema information."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool(persist_directory=temp_dir)
        
        # Test channel query
        results = rag_tool.retrieve("What are the different channels?", k=3)
        
        assert len(results) > 0, "Expected results for channels query"
        assert any("channel" in result.lower() for result in results), \
            "Expected at least one result to mention channels"
        
        print(f"✓ Retrieved {len(results)} results for 'What are the different channels?'")
        print(f"  Top result: {results[0][:100]}...")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_retrieve_with_different_k():
    """Test retrieving different numbers of results."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool(persist_directory=temp_dir)
        
        # Test with k=1
        results_1 = rag_tool.retrieve("What is FICO?", k=1)
        assert len(results_1) == 1, f"Expected 1 result, got {len(results_1)}"
        
        # Test with k=5
        results_5 = rag_tool.retrieve("What is FICO?", k=5)
        assert len(results_5) == 5, f"Expected 5 results, got {len(results_5)}"
        
        print(f"✓ Retrieved correct number of results for k=1 and k=5")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_convenience_function():
    """Test the convenience retrieve function."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Use convenience function
        results = retrieve("What is approval rate?", k=3)
        
        assert len(results) > 0, "Expected results from convenience function"
        assert any("approval rate" in result.lower() for result in results), \
            "Expected at least one result to mention approval rate"
        
        print(f"✓ Convenience function works correctly")
        print(f"  Retrieved {len(results)} results")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_semantic_search_quality():
    """Test that semantic search returns relevant results."""
    # Create temporary directory for testing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Initialize RAG tool
        rag_tool = RAGTool(persist_directory=temp_dir)
        
        # Test various queries
        test_cases = [
            ("What is the difference between submits and approvals?", ["submit", "approval"]),
            ("How do I measure forecast accuracy?", ["forecast", "accuracy"]),
            ("What are FICO bands?", ["fico", "band"]),
            ("Explain the customer funnel", ["funnel", "submission", "approval", "issuance"]),
        ]
        
        for query, expected_terms in test_cases:
            results = rag_tool.retrieve(query, k=3)
            assert len(results) > 0, f"Expected results for query: {query}"
            
            # Check if at least one expected term appears in results
            combined_results = " ".join(results).lower()
            found_terms = [term for term in expected_terms if term in combined_results]
            assert len(found_terms) > 0, \
                f"Expected at least one of {expected_terms} in results for query: {query}"
            
            print(f"✓ Query '{query}' returned relevant results with terms: {found_terms}")
        
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    print("Testing RAG Tool Implementation\n")
    print("=" * 60)
    
    test_rag_tool_initialization()
    print()
    
    test_retrieve_kpi_definition()
    print()
    
    test_retrieve_schema_info()
    print()
    
    test_retrieve_with_different_k()
    print()
    
    test_convenience_function()
    print()
    
    test_semantic_search_quality()
    print()
    
    print("=" * 60)
    print("All tests passed! ✓")
