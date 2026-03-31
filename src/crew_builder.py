from crewai import Crew, Process
from src.agents import TravelAgents
from src.tasks import TravelTasks

class CrewBuilder:
    """
    Orquestra a equipa (Crew) e inicia o processo.
    """
    def __init__(self, destino="", dias=1, origem="", interesses="", settings=None):
        self.destino = destino
        self.dias = dias
        self.origem = origem
        self.interesses = interesses
        self.settings = settings
        self.agents_factory = TravelAgents()
        self.tasks_factory = TravelTasks()

    def create_local_expert_agent(self):
        """Factory method para o teste."""
        return self.agents_factory.local_expert()

    def run(self):
        # 1. Cria os Agentes
        expert = self.agents_factory.local_expert()
        logistics = self.agents_factory.logistics_manager()
        architect = self.agents_factory.itinerary_architect()

        # 2. Cria as Tarefas e atribui aos Agentes
        task_research = self.tasks_factory.research_destination(expert, self.destino, self.interesses)
        task_logistics = self.tasks_factory.calculate_logistics(logistics, self.destino, self.dias, self.origem)
        task_compile = self.tasks_factory.compile_itinerary(architect, self.destino, self.dias, self.interesses)

        # 3. Monta a "Crew" (Equipa)
        crew = Crew(
            agents=[expert, logistics, architect],
            tasks=[task_research, task_logistics, task_compile],
            process=Process.sequential,
            verbose=True
        )

        return crew.kickoff()