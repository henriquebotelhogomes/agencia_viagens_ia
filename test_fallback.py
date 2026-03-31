import asyncio
import os
from src.config import settings

os.environ["GEMINI_API_KEY"] = settings.google_api_key

def test_fallback():
    from litellm import completion
    try:
        response = completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "hello"}],
            api_key="invalid_groq_key", # Fails Groq
            fallbacks=[{"model": "gemini/gemini-1.5-flash", "api_key": settings.google_api_key}]
        )
        print("Fallback worked:", response.model)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_fallback()
