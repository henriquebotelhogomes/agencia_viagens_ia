import os
from src.config import settings
import google.generativeai as genai

def list_gemini_models():
    print(f"Testing with Key: {settings.google_api_key[:10]}...")
    genai.configure(api_key=settings.google_api_key)
    try:
        models = genai.list_models()
        print("\nAvailable Models for this Key:")
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"\nError listing models: {e}")

if __name__ == "__main__":
    list_gemini_models()
