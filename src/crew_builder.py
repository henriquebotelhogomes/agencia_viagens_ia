from typing import Any, Optional, cast

from crewai import Agent, Crew, Process, Task

from src.agents import TravelAgents
from src.tasks import TravelTasks


class CrewBuilder:
    """
    Orquestra a equipa (Crew) e inicia o processo.
    """

    def __init__(
        self,
        destino: str = "",
        dias: int = 1,
        origem: str = "",
        interesses: str = "",
        settings: Any = None,
    ) -> None:
        self.destino = destino
        self.dias = dias
        self.origem = origem
        self.interesses = interesses
        self.settings = settings
        self.agents_factory = TravelAgents()
        self.tasks_factory = TravelTasks()

    def create_local_expert_agent(self) -> Agent:
        """Factory method para o agente Guia Local."""
        return self.agents_factory.local_expert()

    def create_logistics_manager_agent(self) -> Agent:
        """Factory method para o agente Gerente de Logística."""
        return self.agents_factory.logistics_manager()

    def create_itinerary_architect_agent(self) -> Agent:
        """Factory method para o agente Arquiteto de Roteiros."""
        return self.agents_factory.itinerary_architect()

    def create_research_task(self, agent: Agent, destino: str, interesses: str) -> Task:
        """Cria a tarefa de pesquisa."""
        return self.tasks_factory.research_destination(agent, destino, interesses)

    def create_logistics_task(
        self, agent: Agent, destino: str, dias: int, origem: str
    ) -> Task:
        """Cria a tarefa de logística."""
        return self.tasks_factory.calculate_logistics(agent, destino, dias, origem)

    def create_itinerary_task(
        self, agent: Agent, destino: str, dias: int, interesses: str
    ) -> Task:
        """Cria a tarefa de roteiro."""
        return self.tasks_factory.compile_itinerary(agent, destino, dias, interesses)

    def build_crew(
        self,
        destino: str,
        dias: int,
        interesses: str,
        origem: Optional[str] = None,
    ) -> Crew:
        """
        Constrói a equipa (Crew) completa com agentes e tarefas.
        """
        # Se origem não for passada, usa a da instância se existir
        origem = cast(str, origem or getattr(self, "origem", "São Paulo, Brasil"))

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
        # Utiliza o build_crew para manter consistência
        crew = self.build_crew(self.destino, self.dias, self.interesses, self.origem)
        return crew.kickoff()
