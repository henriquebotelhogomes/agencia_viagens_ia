"""Rótulos de moeda e idioma para os prompts (item S14 do PRD / FR-10).

Centraliza o vocabulário de localização usado por tarefas, agentes e UI —
nada de "R$" ou português hardcoded nos prompts.
"""

# Moedas suportadas no briefing (código ISO 4217 -> símbolo usual)
CURRENCY_SYMBOLS: dict[str, str] = {
    "BRL": "R$",
    "USD": "US$",
    "EUR": "€",
    "GBP": "£",
}

# Idiomas suportados no briefing (BCP 47 -> nome por extenso para o prompt)
LANGUAGE_NAMES: dict[str, str] = {
    "pt-BR": "português do Brasil",
    "en-US": "inglês (English)",
    "es-ES": "espanhol (español)",
}

DEFAULT_CURRENCY = "BRL"
DEFAULT_LANGUAGE = "pt-BR"


def currency_label(code: str) -> str:
    """Formata a moeda para uso em prompts. Ex.: ``BRL`` -> ``BRL (R$)``.

    Códigos desconhecidos retornam apenas o próprio código normalizado.
    """
    code = code.strip().upper()
    symbol = CURRENCY_SYMBOLS.get(code)
    return f"{code} ({symbol})" if symbol else code


def language_name(code: str) -> str:
    """Nome do idioma por extenso para o prompt.

    Códigos desconhecidos retornam como estão (o LLM ainda os entende).
    """
    code = code.strip()
    return LANGUAGE_NAMES.get(code, code)
