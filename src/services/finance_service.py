"""Serviços financeiros: câmbio e custos de LLM (FinOps).

Câmbio via **frankfurter.app** (item S5 do PRD): API gratuita do BCE, sem chave.

FinOps (item S4 do PRD): ``estimate_costs_from_usage`` usa **tokens reais** do
``CrewOutput.token_usage``; a heurística por volume de logs permanece apenas
como último recurso (ex.: roteiro servido do cache, sem execução de LLM).
"""

import requests
from loguru import logger

from src.config import Settings, get_settings

# API de câmbio do Banco Central Europeu (gratuita, sem chave)
EXCHANGE_RATE_API_URL = "https://api.frankfurter.dev/v1/latest"
EXCHANGE_RATE_TIMEOUT_SECONDS = 5.0


class FinanceService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def get_exchange_rate(self, base: str, target: str) -> float | None:
        """
        Obtém a taxa de câmbio entre duas moedas via frankfurter.app.
        Retorna ``None`` em caso de falha (com log), sem quebrar o fluxo.
        """
        base = base.strip().upper()
        target = target.strip().upper()
        if not base or not target:
            logger.warning("Câmbio: moedas de origem/destino não informadas.")
            return None
        if base == target:
            return 1.0

        try:
            response = requests.get(
                EXCHANGE_RATE_API_URL,
                params={"base": base, "symbols": target},
                timeout=EXCHANGE_RATE_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
            rate = data.get("rates", {}).get(target)
            if rate is not None:
                return float(rate)
            logger.warning(f"Câmbio: taxa {base}->{target} ausente na resposta.")
        except requests.Timeout:
            logger.warning(f"Câmbio: timeout ao consultar {base}->{target}.")
        except Exception as e:
            logger.warning(f"Câmbio: falha ao consultar {base}->{target}: {e}")
        return None

    def estimate_costs_from_usage(
        self, prompt_tokens: int, completion_tokens: int
    ) -> dict[str, float]:
        """Calcula custos a partir de **tokens reais** (item S4 do PRD).

        Recebe o `usage` agregado da execução (``CrewOutput.token_usage``) e
        devolve o comparativo FinOps: custo no stack atual vs. GPT-4o de
        referência ("custo evitado").
        """
        total_tokens = prompt_tokens + completion_tokens

        custo_gpt4o = (prompt_tokens / 1_000_000 * self.settings.price_gpt4o_input) + (
            completion_tokens / 1_000_000 * self.settings.price_gpt4o_output
        )
        custo_stack = (prompt_tokens / 1_000_000 * self.settings.price_groq_input) + (
            completion_tokens / 1_000_000 * self.settings.price_groq_output
        )

        return {
            "total_tokens": float(total_tokens),
            "custo_gpt4o": custo_gpt4o,
            "custo_groq": custo_stack,
            "savings": custo_gpt4o - custo_stack,
        }

    def estimate_costs(self, logs_text: str) -> dict[str, float]:
        """
        Estima custos pela heurística de volume de logs (último recurso).

        Prefira ``estimate_costs_from_usage`` com tokens reais; esta versão só
        é usada quando não houve execução de LLM (ex.: cache hit).
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
