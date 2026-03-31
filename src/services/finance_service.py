from typing import Dict, Optional

from src.config import settings


class FinanceService:
    def __init__(self) -> None:
        self.settings = settings

    def get_exchange_rate(self, base: str, target: str) -> Optional[float]:
        """
        Calcula a taxa de câmbio entre duas moedas via API Exchangerates.
        Mocado nos testes via requests.get.
        """
        try:
            import requests  # type: ignore

            response = requests.get(
                f"https://api.exchangeratesapi.io/v1/latest?base={base}"
            )
            data = response.json()
            if target in data.get("rates", {}):
                return float(data["rates"][target])
        except Exception:
            pass
        return None

    def estimate_costs(self, logs_text: str) -> Dict[str, float]:
        """
        Calcula os custos estimados com base no volume de logs gerados pelos agentes.
        Esta é uma heurística simples para observabilidade FinOps.
        """
        if not isinstance(logs_text, str):
            raise TypeError("Logs must be string")

        # Heurística profissional: 0.55 tokens/char + overhead base
        # (10.000 chars -> 5.500 + 2.500 = 8.000 tokens)
        total_tokens = int(len(logs_text) * 0.55) + 2500
        prompt_tokens = int(total_tokens * 0.8)
        completion_tokens = int(total_tokens * 0.2)

        custo_gpt4o = (prompt_tokens / 1_000_000 * self.settings.price_gpt4o_input) + (
            completion_tokens / 1_000_000 * self.settings.price_gpt4o_output
        )

        custo_groq = (prompt_tokens / 1_000_000 * self.settings.price_groq_input) + (
            completion_tokens / 1_000_000 * self.settings.price_groq_output
        )

        return {
            "total_tokens": float(total_tokens),
            "custo_gpt4o": custo_gpt4o,
            "custo_groq": custo_groq,
            "savings": custo_gpt4o - custo_groq,
        }
