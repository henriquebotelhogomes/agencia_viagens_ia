from crewai import Agent, Task


class TravelTasks:
    def research_destination(self, agent: Agent, destino: str, interesses: str) -> Task:
        return Task(
            description=(
                f"Pesquise {destino}. Interesses: {interesses}. "
                f"Liste até 5 atrações e 3 restaurantes com descrição de 1 linha cada."
            ),
            expected_output=(
                "Lista com 5 atrações e 3 restaurantes. Máximo 200 palavras."
            ),
            agent=agent,
        )

    def calculate_logistics(
        self, agent: Agent, destino: str, dias: int, origem: str
    ) -> Task:
        return Task(
            description=(
                f"Para {dias} dias em {destino}, calcule custos detalhados: "
                f"1. VOO: Nome de uma companhia que opere o trecho "
                f"{origem}->{destino}. "
                f"2. HOTEL: Nome de um hotel (+ estrelas) em {destino}. "
                f"3. ALIMENTAÇÃO: Detalhe o que compõe o gasto diário "
                "(café/almoço/jantar)."
            ),
            expected_output=(
                "Tabela em BRL (R$) com: Companhia Aérea, Nome do Hotel e estrelas, "
                "Detalhe da Alimentação/dia, TARIFA (R$) por item e TOTAL estimado."
            ),
            agent=agent,
        )

    def compile_itinerary(
        self, agent: Agent, destino: str, dias: int, interesses: str
    ) -> Task:
        return Task(
            description=(
                f"Crie roteiro de {dias} dias em {destino} com foco em: "
                f"{interesses}. Use EXATAMENTE a tabela de custos detalhada "
                "em REAIS (R$) gerada pelo colega logístico."
            ),
            expected_output=(
                "Roteiro Markdown completo com: Título atrativo, Tabela de "
                "Custos Detalhada em R$, Cronograma de {dias} dias "
                "(manhã/tarde/noite) e dicas exclusivas. "
                "A moeda deve ser exclusivamente R$."
            ),
            agent=agent,
        )
