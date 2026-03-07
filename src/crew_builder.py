from crewai import Crew, Process
from src.agents import TravelAgents
from src.tasks import TravelTasks

class TravelCrew:
    """
    Orquestra a equipa (Crew) e inicia o processo.
    """
    def __init__(self, destino, dias, origem, interesses):
        self.destino = destino
        self.dias = dias
        self.origem = origem
        self.interesses = interesses

    def run(self):
        # 1. Instancia Fábricas
        agents = TravelAgents()
        tasks = TravelTasks()

        # 2. Cria os Agentes
        expert = agents.local_expert()
        logistics = agents.logistics_manager()
        architect = agents.itinerary_architect()

        # 3. Cria as Tarefas e atribui aos Agentes
        task_research = tasks.research_destination(expert, self.destino, self.interesses)
        task_logistics = tasks.calculate_logistics(logistics, self.destino, self.dias, self.origem)
        task_compile = tasks.compile_itinerary(architect, self.destino, self.dias, self.interesses)

        # 4. Monta a "Crew" (Equipa)
        # O processo SEQUENTIAL garante que a logística aguarda a pesquisa terminar.
        crew = Crew(
            agents=[expert, logistics, architect],
            tasks=[task_research, task_logistics, task_compile],
            process=Process.sequential,
            verbose=True
        )

        # 5. Dá o pontapé de saída (Kickoff)
        result = crew.kickoff()
        return result