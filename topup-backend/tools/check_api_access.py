"""
Check OpenAI API access and available models.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import openai


def check_api_key():
    """Check if API key is set."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
    
    print(f"✓ OPENAI_API_KEY found (length: {len(api_key)})")
    return True


def check_available_models():
    """Check what models are available with this API key."""
    try:
        client = openai.OpenAI()
        
        print("\nChecking available models...")
        models = client.models.list()
        
        # Filter for embedding models
        embedding_models = [m.id for m in models.data if 'embed' in m.id.lower()]
        
        if embedding_models:
            print(f"\n✓ Found {len(embedding_models)} embedding models:")
            for model in embedding_models:
                print(f"  - {model}")
        else:
            print("\n⚠ No embedding models found")
            print("  This API key may not have access to embedding models")
        
        # Check for specific models
        all_model_ids = [m.id for m in models.data]
        
        print("\nChecking specific embedding models:")
        models_to_check = [
            "text-embedding-3-small",
            "text-embedding-3-large",
            "text-embedding-ada-002"
        ]
        
        for model in models_to_check:
            if model in all_model_ids:
                print(f"  ✓ {model} - Available")
            else:
                print(f"  ✗ {model} - Not available")
        
        return True
        
    except openai.AuthenticationError as e:
        print(f"\n❌ Authentication Error: {e}")
        print("  The API key may be invalid or expired")
        return False
    except openai.PermissionDeniedError as e:
        print(f"\n❌ Permission Denied: {e}")
        print("  The API key doesn't have the required permissions")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def test_embedding_call():
    """Test a simple embedding call."""
    try:
        client = openai.OpenAI()
        
        print("\nTesting embedding call with text-embedding-ada-002...")
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input="test"
        )
        
        print(f"✓ Embedding call successful")
        print(f"  Embedding dimension: {len(response.data[0].embedding)}")
        return True
        
    except openai.PermissionDeniedError as e:
        print(f"✗ Permission denied for text-embedding-ada-002")
        print(f"  Error: {e}")
        
        # Try alternative model
        try:
            print("\nTrying text-embedding-3-small...")
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            print(f"✓ text-embedding-3-small works!")
            print(f"  Embedding dimension: {len(response.data[0].embedding)}")
            return True
        except Exception as e2:
            print(f"✗ text-embedding-3-small also failed: {e2}")
            return False
            
    except Exception as e:
        print(f"✗ Embedding call failed: {e}")
        return False


def main():
    print("=" * 60)
    print("OpenAI API Access Check")
    print("=" * 60)
    print()
    
    if not check_api_key():
        return 1
    
    if not check_available_models():
        return 1
    
    if not test_embedding_call():
        print("\n" + "=" * 60)
        print("⚠ WARNING: Embedding models not accessible")
        print("=" * 60)
        print("\nPossible solutions:")
        print("1. Check if your OpenAI account has credits")
        print("2. Verify your API key has the correct permissions")
        print("3. Try generating a new API key from OpenAI dashboard")
        print("4. Check if your account tier supports embedding models")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ API Access Verified")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
