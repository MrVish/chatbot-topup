"""
Simple test to verify embedding API access.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import openai


def test_embedding_simple():
    """Test a simple embedding call."""
    print("Testing OpenAI Embedding API Access")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"✓ API Key found (length: {len(api_key)})")
    print()
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        print("Attempting to create embedding with text-embedding-3-small...")
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test query"
        )
        
        embedding = response.data[0].embedding
        print(f"✅ SUCCESS!")
        print(f"   Embedding dimension: {len(embedding)}")
        print(f"   Model used: {response.model}")
        print(f"   Usage: {response.usage.total_tokens} tokens")
        print()
        return True
        
    except openai.AuthenticationError as e:
        print(f"❌ Authentication Error")
        print(f"   {e}")
        print()
        print("   Solution: Check if API key is valid")
        return False
        
    except openai.PermissionDeniedError as e:
        print(f"❌ Permission Denied")
        print(f"   {e}")
        print()
        print("   Possible causes:")
        print("   1. Account has no credits/billing not set up")
        print("   2. API key doesn't have embedding permissions")
        print("   3. Free tier limitations")
        print()
        print("   Solutions:")
        print("   1. Add payment method at https://platform.openai.com/account/billing")
        print("   2. Add credits to your account")
        print("   3. Generate a new API key with full permissions")
        return False
        
    except openai.RateLimitError as e:
        print(f"❌ Rate Limit Error")
        print(f"   {e}")
        print()
        print("   Solution: Wait a moment and try again")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error")
        print(f"   {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = test_embedding_simple()
    exit(0 if success else 1)
