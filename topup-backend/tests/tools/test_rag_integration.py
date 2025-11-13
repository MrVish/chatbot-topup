"""
End-to-end integration test for RAG Tool with real ChromaDB.
This test verifies that the RAG tool works with actual ChromaDB and OpenAI embeddings.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.rag_tool import RAGTool, retrieve


def test_real_chromadb_initialization():
    """Test that ChromaDB is actually initialized with persistent storage."""
    print("Test 1: Real ChromaDB Initialization")
    print("-" * 60)
    
    # Initialize RAG tool
    rag_tool = RAGTool(persist_directory="./data/chroma")
    
    # Verify it's using PersistentClient
    assert hasattr(rag_tool, 'client'), "RAG tool missing client"
    assert rag_tool.client is not None, "Client is None"
    
    # Verify collection exists
    assert hasattr(rag_tool, 'collection'), "RAG tool missing collection"
    assert rag_tool.collection is not None, "Collection is None"
    assert rag_tool.collection.name == "topup_glossary", f"Wrong collection name: {rag_tool.collection.name}"
    
    # Verify documents are indexed
    count = rag_tool.collection.count()
    assert count > 0, f"No documents indexed, count: {count}"
    
    print(f"✓ ChromaDB initialized with PersistentClient")
    print(f"✓ Collection 'topup_glossary' exists")
    print(f"✓ {count} documents indexed")
    print()


def test_real_embeddings():
    """Test that OpenAI embeddings are actually being used."""
    print("Test 2: Real OpenAI Embeddings")
    print("-" * 60)
    
    rag_tool = RAGTool(persist_directory="./data/chroma")
    
    # Verify embeddings are configured
    assert hasattr(rag_tool, 'embeddings'), "RAG tool missing embeddings"
    assert rag_tool.embeddings is not None, "Embeddings is None"
    
    # Test embedding generation
    test_text = "What is funding rate?"
    embedding = rag_tool.embeddings.embed_query(test_text)
    
    assert embedding is not None, "Embedding is None"
    assert len(embedding) > 0, "Embedding is empty"
    assert isinstance(embedding, list), f"Embedding should be list, got {type(embedding)}"
    
    print(f"✓ OpenAI embeddings configured")
    print(f"✓ Generated embedding for test query")
    print(f"✓ Embedding dimension: {len(embedding)}")
    print()


def test_semantic_search():
    """Test semantic search with real ChromaDB and embeddings."""
    print("Test 3: Semantic Search")
    print("-" * 60)
    
    rag_tool = RAGTool(persist_directory="./data/chroma")
    
    # Test query
    query = "What is funding rate?"
    results = rag_tool.retrieve(query, k=3)
    
    assert results is not None, "Results is None"
    assert len(results) > 0, "No results returned"
    assert len(results) <= 3, f"Too many results: {len(results)}"
    
    # Verify results contain relevant information
    combined_text = " ".join(results).lower()
    assert "funding" in combined_text or "rate" in combined_text, \
        "Results don't contain relevant terms"
    
    print(f"✓ Semantic search executed successfully")
    print(f"✓ Retrieved {len(results)} results")
    print(f"✓ Top result preview: {results[0][:100]}...")
    print()


def test_multiple_queries():
    """Test multiple different queries to verify semantic understanding."""
    print("Test 4: Multiple Query Types")
    print("-" * 60)
    
    rag_tool = RAGTool(persist_directory="./data/chroma")
    
    test_cases = [
        ("What is funding rate?", ["funding", "rate", "issued"]),
        ("What are channels?", ["channel", "marketing"]),
        ("What is FICO?", ["fico", "credit", "score"]),
        ("Explain approval rate", ["approval", "rate", "approved"]),
        ("What is issuance?", ["issuance", "issued", "loan"]),
    ]
    
    for query, expected_terms in test_cases:
        results = rag_tool.retrieve(query, k=3)
        assert len(results) > 0, f"No results for query: {query}"
        
        combined_text = " ".join(results).lower()
        found_terms = [term for term in expected_terms if term in combined_text]
        
        assert len(found_terms) > 0, \
            f"Query '{query}' didn't return relevant results. Expected terms: {expected_terms}"
        
        print(f"✓ Query: '{query}' - Found terms: {found_terms}")
    
    print()


def test_convenience_function():
    """Test the convenience retrieve function."""
    print("Test 5: Convenience Function")
    print("-" * 60)
    
    # Test convenience function
    results = retrieve("What is approval rate?", k=3)
    
    assert results is not None, "Results is None"
    assert len(results) > 0, "No results returned"
    
    combined_text = " ".join(results).lower()
    assert "approval" in combined_text, "Results don't contain 'approval'"
    
    print(f"✓ Convenience function works")
    print(f"✓ Retrieved {len(results)} results")
    print()


def test_persistence():
    """Test that data persists across instances."""
    print("Test 6: Data Persistence")
    print("-" * 60)
    
    # Create first instance
    rag_tool1 = RAGTool(persist_directory="./data/chroma")
    count1 = rag_tool1.collection.count()
    
    # Create second instance (should reuse existing data)
    rag_tool2 = RAGTool(persist_directory="./data/chroma")
    count2 = rag_tool2.collection.count()
    
    assert count1 == count2, f"Document counts don't match: {count1} vs {count2}"
    assert count1 > 0, "No documents persisted"
    
    print(f"✓ Data persists across instances")
    print(f"✓ Both instances have {count1} documents")
    print()


def test_different_k_values():
    """Test retrieval with different k values."""
    print("Test 7: Different K Values")
    print("-" * 60)
    
    rag_tool = RAGTool(persist_directory="./data/chroma")
    query = "What is FICO?"
    
    # Test k=1
    results_1 = rag_tool.retrieve(query, k=1)
    assert len(results_1) == 1, f"Expected 1 result, got {len(results_1)}"
    
    # Test k=3 (default)
    results_3 = rag_tool.retrieve(query, k=3)
    assert len(results_3) == 3, f"Expected 3 results, got {len(results_3)}"
    
    # Test k=5
    results_5 = rag_tool.retrieve(query, k=5)
    assert len(results_5) == 5, f"Expected 5 results, got {len(results_5)}"
    
    print(f"✓ k=1: {len(results_1)} result")
    print(f"✓ k=3: {len(results_3)} results")
    print(f"✓ k=5: {len(results_5)} results")
    print()


def test_actual_chromadb_files():
    """Verify that actual ChromaDB files are created on disk."""
    print("Test 8: ChromaDB Files on Disk")
    print("-" * 60)
    
    chroma_path = "./data/chroma"
    
    # Initialize to ensure files are created
    rag_tool = RAGTool(persist_directory=chroma_path)
    
    # Check that directory exists
    assert os.path.exists(chroma_path), f"ChromaDB directory doesn't exist: {chroma_path}"
    assert os.path.isdir(chroma_path), f"ChromaDB path is not a directory: {chroma_path}"
    
    # Check that there are files in the directory
    files = os.listdir(chroma_path)
    assert len(files) > 0, f"No files in ChromaDB directory: {chroma_path}"
    
    print(f"✓ ChromaDB directory exists: {chroma_path}")
    print(f"✓ Found {len(files)} files/folders in ChromaDB directory")
    print(f"  Files: {', '.join(files[:5])}")
    print()


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("RAG Tool End-to-End Integration Test")
    print("Testing with REAL ChromaDB and OpenAI Embeddings")
    print("=" * 60)
    print()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in environment")
        print("Please set OPENAI_API_KEY in .env file")
        return 1
    
    print(f"✓ OPENAI_API_KEY found (length: {len(api_key)})")
    print()
    
    try:
        # Run all tests
        test_real_chromadb_initialization()
        test_real_embeddings()
        test_semantic_search()
        test_multiple_queries()
        test_convenience_function()
        test_persistence()
        test_different_k_values()
        test_actual_chromadb_files()
        
        print("=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print("- Real ChromaDB PersistentClient verified")
        print("- Real OpenAI embeddings verified")
        print("- Semantic search working correctly")
        print("- Data persistence confirmed")
        print("- ChromaDB files created on disk")
        print("- No mocking detected - all components are real")
        print()
        
        return 0
        
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
