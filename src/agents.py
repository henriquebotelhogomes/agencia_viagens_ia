import os
from typing import Any

from crewai import LLM, Agent
from crewai_tools import SerperDevTool

from src.config import settings

# Injeta a chave do Google no ambiente para o LiteLLM (Plano B)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key
os.environ["GEMINI_API_KEY"] = settings.google_api_key


class TravelAgents:
    def __init__(self, settings: Any = None) -> None:
        from src.config import settings as default_settings

        self.settings = settings or default_settings

        # Modelo PRO: Plano A (Groq 70B) -> Plano B (Gemini 1.5 Pro)
        self.llm_pro = LLM(
            model=self.settings.model_pro,
            api_key=self.settings.groq_api_key,
            temperature=0.3,
            max_retries=2,
            # Plano B e C configurados via fallbacks com chaves explícitas
            fallbacks=[
                {
                    "model": self.settings.model_pro_fallback,
                    "api_key": self.settings.google_api_key,
                },
                {
                    "model": "groq/llama-3.1-8b-instant",
                    "api_key": self.settings.groq_api_key,
                },
            ],
        )

        # Modelo FAST: Plano A (Groq 8B) -> Plano B (Gemini 1.5 Flash)
        self.llm_fast = LLM(
            model=self.settings.model_fast,
            api_key=self.settings.groq_api_key,
            temperature=0.2,
            max_retries=2,
            fallbacks=[
                {
                    "model": self.settings.model_fast_fallback,
                    "api_key": self.settings.google_api_key,
                },
                {
                    "model": self.settings.model_pro_fallback,
                    "api_key": self.settings.google_api_key,
                },
            ],
        )

        self.search_tool = SerperDevTool()

    def local_expert(self) -> Agent:
        return Agent(
            role="Guia Local",
            goal=(
                "Fornecer informações detalhadas sobre {destino} baseadas em "
                "{interesses}."
            ),
            backstory=(
                "Um guia local experiente que conhece todos os segredos de {destino}."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm_fast,
            max_iter=3,
        )

    def logistics_manager(self) -> Agent:
        return Agent(
            role="Gerente de Logística",
            goal="Estimar custos detalhados em REAIS (R$) para a viagem em {destino}.",
            backstory=(
                "Analista financeiro especializado em turismo. "
                "Você não aceita valores genéricos. "
                "Você busca sempre nomes de companhias aéreas reais, "
                "nomes de hotéis com suas estrelas "
                "e detalha as refeições (café, almoço, jantar) "
                "para compor o custo diário. "
                "Tudo deve ser calculado e exibido em REAIS (R$)."
            ),
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast,
            max_iter=3,
        )

    def itinerary_architect(self) -> Agent:
        return Agent(
            role="Arquiteto de Roteiros",
            goal="Criar roteiro de {dias} dias em {destino}.",
            backstory=(
                "Arquiteto de roteiros premium com redundância de "
                "modelos (Plano A, B e C)."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self.llm_pro,
            max_iter=3,
        )
