from typing import Dict
from src.config import settings

class FinanceService:
    def __init__(self):
        self.settings = settings

    def estimate_costs(self, logs_text: str) -> Dict[str, float]:
        """
        Calcula os custos estimados com base no volume de logs gerados pelos agentes.
        Esta é uma heurística simples, já que o CrewAI não exporta o consumo exato facilmente 
        sem instrumentação profunda.
        """
        # Heurística: 1 caractere de log ~ 0.33 tokens + overhead de prompts base
        total_tokens = len(logs_text) // 3 + 2500
        prompt_tokens = int(total_tokens * 0.8)
        completion_tokens = int(total_tokens * 0.2)

        custo_gpt4o = (
            (prompt_tokens / 1_000_000 * self.settings.price_gpt4o_input) +
            (completion_tokens / 1_000_000 * self.settings.price_gpt4o_output)
        )
        
        custo_groq = (
            (prompt_tokens / 1_000_000 * self.settings.price_groq_input) +
            (completion_tokens / 1_000_000 * self.settings.price_groq_output)
        )

        return {
            "total_tokens": float(total_tokens),
            "custo_gpt4o": custo_gpt4o,
            "custo_groq": custo_groq,
            "savings": custo_gpt4o - custo_groq
        }
