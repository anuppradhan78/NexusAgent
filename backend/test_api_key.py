#!/usr/bin/env python3
"""
Quick test to check which Claude models work with your API key
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=api_key)

# Models to test
models_to_test = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]

print("Testing Claude API models...")
print(f"API Key: {api_key[:20]}...")
print("-" * 60)

for model in models_to_test:
    try:
        print(f"\nTesting: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"✅ SUCCESS - {model} works!")
        print(f"   Response: {response.content[0].text}")
        break  # Stop after first success
    except Exception as e:
        error_str = str(e)
        if "not_found_error" in error_str:
            print(f"❌ FAILED - Model not found")
        elif "permission" in error_str.lower():
            print(f"❌ FAILED - No permission")
        else:
            print(f"❌ FAILED - {error_str[:100]}")

print("\n" + "-" * 60)
print("Test complete!")
