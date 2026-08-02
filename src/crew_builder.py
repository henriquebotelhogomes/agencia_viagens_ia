"""Orquestração da equipe (Crew) de planejamento de viagens."""

from typing import Any

from crewai import Agent, Crew, Process, Task
from loguru import logger

from src.agents import TravelAgents
from src.config import Settings
from src.tasks import TravelTasks
from src.utils.localization import DEFAULT_CURRENCY, DEFAULT_LANGUAGE


class CrewBuilder:
    """
    Orquestra a equipa (Crew) e inicia o processo.

    A configuração é injetada (item S2 do PRD); quando omitida, os componentes
    resolvem a configuração padrão sob demanda.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        destino: str = "",
        dias: int = 1,
        origem: str = "",
        interesses: str = "",
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
        use_fallback: bool = False,
        refine_instruction: str | None = None,
        previous_itinerary: str | None = None,
    ) -> None:
        self.settings = settings
        self.destino = destino
        self.dias = dias
        self.origem = origem
        self.interesses = interesses
        self.moeda = moeda
        self.idioma = idioma
        self.use_fallback = use_fallback
        self.refine_instruction = refine_instruction
        self.previous_itinerary = previous_itinerary
        self.agents_factory = TravelAgents(settings, use_fallback=use_fallback)
        self.tasks_factory = TravelTasks()
        # Bloco de contexto injetado nas tasks quando é um refine
        self._refine_context: str | None = None
        if refine_instruction and previous_itinerary:
            self._refine_context = (
                "CONTEXTO DE REFINAMENTO:\n"
                f"Roteiro atual:\n{previous_itinerary}\n\n"
                f"Instrução do usuário: {refine_instruction}\n"
                "Aplique a instrução mantendo o que funciona no roteiro."
            )

    def create_local_expert_agent(self) -> Agent:
        """Factory method para o agente Guia Local."""
        return self.agents_factory.local_expert()

    def create_logistics_manager_agent(self) -> Agent:
        """Factory method para o agente Gerente de Logística."""
        return self.agents_factory.logistics_manager(moeda=self.moeda)

    def create_itinerary_architect_agent(self) -> Agent:
        """Factory method para o agente Arquiteto de Roteiros."""
        return self.agents_factory.itinerary_architect()

    def create_research_task(self, agent: Agent, destino: str, interesses: str) -> Task:
        """Cria a tarefa de pesquisa."""
        return self.tasks_factory.research_destination(
            agent,
            destino,
            interesses,
            idioma=self.idioma,
            refine_context=self._refine_context,
        )

    def create_logistics_task(
        self, agent: Agent, destino: str, dias: int, origem: str
    ) -> Task:
        """Cria a tarefa de logística."""
        return self.tasks_factory.calculate_logistics(
            agent,
            destino,
            dias,
            origem,
            moeda=self.moeda,
            idioma=self.idioma,
            refine_context=self._refine_context,
        )

    def create_itinerary_task(
        self, agent: Agent, destino: str, dias: int, interesses: str
    ) -> Task:
        """Cria a tarefa de roteiro."""
        return self.tasks_factory.compile_itinerary(
            agent,
            destino,
            dias,
            interesses,
            moeda=self.moeda,
            idioma=self.idioma,
            refine_context=self._refine_context,
        )

    def build_crew(
        self,
        destino: str,
        dias: int,
        interesses: str,
        origem: str | None = None,
    ) -> Crew:
        """
        Constrói a equipa (Crew) completa com agentes e tarefas.
        """
        # Se origem não for passada, usa a da instância
        origem = origem or self.origem

        # 1. Cria os Agentes
        expert = self.create_local_expert_agent()
        logistics = self.create_logistics_manager_agent()
        architect = self.create_itinerary_architect_agent()

        # 2. Cria as Tarefas
        task_research = self.create_research_task(expert, destino, interesses)
        task_logistics = self.create_logistics_task(logistics, destino, dias, origem)
        task_itinerary = self.create_itinerary_task(
            architect, destino, dias, interesses
        )

        # 3. Monta a Crew
        return Crew(
            agents=[expert, logistics, architect],
            tasks=[task_research, task_logistics, task_itinerary],
            process=Process.sequential,
            verbose=True,
            cache=False,  # Desativa o cache nativo problemático
        )

    def run(self) -> Any:
        """Executa a crew com failover de gateway de LLM (PRD D2).

        Tenta o gateway primário (OpenCode Go) e, em qualquer falha — `429`,
        teto de orçamento, indisponibilidade —, repete uma vez no OpenRouter.
        Assim a demo nunca bloqueia por causa da cota compartilhada do Go.
        """
        crew = self.build_crew(self.destino, self.dias, self.interesses, self.origem)
        try:
            return crew.kickoff()
        except Exception as e:
            if self.use_fallback:
                raise  # já estamos no fallback: propaga
            logger.warning(
                f"Gateway primário de LLM falhou ({e}); "
                "repetindo a execução no OpenRouter."
            )
            fallback_builder = CrewBuilder(
                self.settings,
                destino=self.destino,
                dias=self.dias,
                origem=self.origem,
                interesses=self.interesses,
                moeda=self.moeda,
                idioma=self.idioma,
                use_fallback=True,
                refine_instruction=self.refine_instruction,
                previous_itinerary=self.previous_itinerary,
            )
            return fallback_builder.run()
