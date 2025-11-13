"""
Check which models are available with the current API key.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("No API key found")
    exit(1)

client = OpenAI(api_key=api_key)

print("="*80)
print("Checking Available Models")
print("="*80)

# Try different models
models_to_test = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
]

for model in models_to_test:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print(f"✓ {model} - AVAILABLE")
    except Exception as e:
        error_msg = str(e)
        if "does not have access" in error_msg or "model_not_found" in error_msg:
            print(f"✗ {model} - NOT ACCESSIBLE")
        else:
            print(f"✗ {model} - ERROR: {error_msg[:50]}")

print("="*80)
