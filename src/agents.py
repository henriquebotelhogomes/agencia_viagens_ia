import os
from crewai import Agent, LLM
from crewai_tools import SerperDevTool
from src.config import settings

# Injeta a chave do Google no ambiente para o LiteLLM (Plano B)
os.environ["GOOGLE_API_KEY"] = settings.google_api_key
os.environ["GEMINI_API_KEY"] = settings.google_api_key

class TravelAgents:

    def __init__(self):
        # Modelo PRO: Plano A (Groq 70B) -> Plano B (Gemini 1.5 Pro)
        self.llm_pro = LLM(
            model=settings.model_pro,
            api_key=settings.groq_api_key,
            temperature=0.3,
            max_retries=2,
            # Plano B e C configurados via fallbacks com chaves explícitas
            fallbacks=[
                {"model": settings.model_pro_fallback, "api_key": settings.google_api_key},
                {"model": "groq/llama-3.1-8b-instant", "api_key": settings.groq_api_key}
            ]
        )

        # Modelo FAST: Plano A (Groq 8B) -> Plano B (Gemini 1.5 Flash)
        self.llm_fast = LLM(
            model=settings.model_fast,
            api_key=settings.groq_api_key,
            temperature=0.2,
            max_retries=2,
            fallbacks=[
                {"model": settings.model_fast_fallback, "api_key": settings.google_api_key},
                {"model": settings.model_pro_fallback, "api_key": settings.google_api_key}
            ]
        )

        self.search_tool = SerperDevTool()

    def local_expert(self):
        return Agent(
            role="Guia Local",
            goal="Listar atrações e restaurantes em {destino} (citar nomes completos).",
            backstory="Especialista em viagens com acesso a múltiplos provedores de IA (Groq/Gemini).",
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast,
            max_iter=3
        )

    def logistics_manager(self):
        return Agent(
            role="Analista de Custos e Logística",
            goal="Estimar custos detalhados em REAIS (R$) para a viagem em {destino}.",
            backstory=(
                "Analista financeiro especializado em turismo. Você não aceita valores genéricos. "
                "Você busca sempre nomes de companhias aéreas reais, nomes de hotéis com suas estrelas "
                "e detalha as refeições (café, almoço, jantar) para compor o custo diário. "
                "Tudo deve ser calculado e exibido em REAIS (R$)."
            ),
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast,
            max_iter=3
        )

    def itinerary_architect(self):
        return Agent(
            role="Criador de Roteiros",
            goal="Criar roteiro de {dias} dias em {destino}.",
            backstory="Arquiteto de roteiros premium com redundância de modelos (Plano A, B e C).",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_pro,
            max_iter=3
        )
