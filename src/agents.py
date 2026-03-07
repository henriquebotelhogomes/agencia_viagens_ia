import os
from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, LLM
from crewai_tools import SerperDevTool


class TravelAgents:

    def __init__(self):
        groq_key = os.getenv("GROQ_API_KEY")

        self.llm_pro = LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.3,
            max_tokens=1024
        )

        self.llm_fast = LLM(
            model="groq/llama-3.3-70b-versatile",
            api_key=groq_key,
            temperature=0.2,
            max_tokens=512
        )

        self.search_tool = SerperDevTool()

    def local_expert(self):
        return Agent(
            role="Guia Local",
            goal="Listar atrações e restaurantes em {destino}.",
            backstory="Guia objetivo. Respostas curtas e diretas.",
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast,
            max_iter=2
        )

    def logistics_manager(self):
        return Agent(
            role="Analista de Custos",
            goal="Estimar custos de viagem para {destino}.",
            backstory="Analista objetivo. Apenas números e estimativas.",
            verbose=True,
            allow_delegation=False,
            tools=[self.search_tool],
            llm=self.llm_fast,
            max_iter=2
        )

    def itinerary_architect(self):
        return Agent(
            role="Criador de Roteiros",
            goal="Criar roteiro de {dias} dias em {destino}.",
            backstory="Escritor de roteiros em Markdown.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm_pro,
            max_iter=2
        )
