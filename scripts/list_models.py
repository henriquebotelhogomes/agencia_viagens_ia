"""Utilitário de diagnóstico: lista os modelos Gemini disponíveis para a chave.

Uso (a partir da raiz do projeto):
    uv run python -m scripts.list_models
"""

import google.generativeai as genai

from src.config import get_settings


def list_gemini_models() -> None:
    settings = get_settings()
    if not settings.google_api_key:
        print("GOOGLE_API_KEY não configurada no .env — nada a listar.")
        return

    print(f"Testing with Key: {settings.google_api_key[:10]}...")
    genai.configure(api_key=settings.google_api_key)
    try:
        models = genai.list_models()
        print("\nAvailable Models for this Key:")
        for m in models:
            if "generateContent" in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"\nError listing models: {e}")


if __name__ == "__main__":
    list_gemini_models()
