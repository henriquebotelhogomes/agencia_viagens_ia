from crewai import Task


class TravelTasks:

    def research_destination(self, agent, destino, interesses):
        return Task(
            description=(
                f"Pesquise {destino}. Interesses: {interesses}. "
                f"Liste até 5 atrações e 3 restaurantes com descrição de 1 linha cada."
            ),
            expected_output=(
                "Lista com 5 atrações e 3 restaurantes. Máximo 200 palavras."
            ),
            agent=agent
        )

    def calculate_logistics(self, agent, destino, dias, origem):
        return Task(
            description=(
                f"Estime custos para {dias} dias de {origem} a {destino}: "
                f"voo, hotel 3 estrelas/noite, alimentação/dia."
            ),
            expected_output=(
                "Tabela com: voo (USD), hotel/noite (USD), alimentação/dia (USD), total estimado. "
                "Máximo 100 palavras."
            ),
            agent=agent
        )

    def compile_itinerary(self, agent, destino, dias, interesses):
        return Task(
            description=(
                f"Crie roteiro de {dias} dias em {destino} com foco em: {interesses}. "
                f"Use os dados dos agentes anteriores."
            ),
            expected_output=(
                f"Roteiro em Markdown com: título, tabela de custos, {dias} dias (manhã/tarde/noite), "
                f"3 dicas. Seja conciso."
            ),
            agent=agent
        )
