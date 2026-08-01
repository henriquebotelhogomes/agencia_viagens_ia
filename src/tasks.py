"""Fábrica de tarefas da equipe de viagens.

Moeda e idioma são parâmetros do briefing (item S14 do PRD / FR-10): nenhum
"R$" ou idioma fica hardcoded nos prompts.
"""

from crewai import Agent, Task

from src.utils.localization import (
    DEFAULT_CURRENCY,
    DEFAULT_LANGUAGE,
    currency_label,
    language_name,
)


class TravelTasks:
    def research_destination(
        self,
        agent: Agent,
        destino: str,
        interesses: str,
        idioma: str = DEFAULT_LANGUAGE,
        refine_context: str | None = None,
    ) -> Task:
        description = (
            f"Pesquise {destino}. Interesses: {interesses}. "
            f"Liste até 5 atrações e 3 restaurantes com descrição de 1 linha "
            f"cada. Escreva a resposta em {language_name(idioma)}."
        )
        if refine_context:
            description += f"\n\n{refine_context}"
        return Task(
            description=description,
            expected_output=(
                "Lista com 5 atrações e 3 restaurantes. Máximo 200 palavras. "
                f"Idioma: {language_name(idioma)}."
            ),
            agent=agent,
        )

    def calculate_logistics(
        self,
        agent: Agent,
        destino: str,
        dias: int,
        origem: str,
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
        refine_context: str | None = None,
    ) -> Task:
        moeda_txt = currency_label(moeda)
        description = (
            f"Para {dias} dias em {destino}, calcule custos detalhados: "
            f"1. VOO: Nome de uma companhia que opere o trecho "
            f"{origem}->{destino}. "
            f"2. HOTEL: Nome de um hotel (+ estrelas) em {destino}. "
            f"3. ALIMENTAÇÃO: Detalhe o que compõe o gasto diário "
            "(café/almoço/jantar). "
            f"Converta e exiba TODOS os valores em {moeda_txt}. "
            f"Escreva a resposta em {language_name(idioma)}."
        )
        if refine_context:
            description += f"\n\n{refine_context}"
        return Task(
            description=description,
            expected_output=(
                f"Tabela em {moeda_txt} com: Companhia Aérea, Nome do Hotel e "
                "estrelas, Detalhe da Alimentação/dia, TARIFA por item e TOTAL "
                f"estimado. Idioma: {language_name(idioma)}."
            ),
            agent=agent,
        )

    def compile_itinerary(
        self,
        agent: Agent,
        destino: str,
        dias: int,
        interesses: str,
        moeda: str = DEFAULT_CURRENCY,
        idioma: str = DEFAULT_LANGUAGE,
        refine_context: str | None = None,
    ) -> Task:
        moeda_txt = currency_label(moeda)
        description = (
            f"Crie roteiro de {dias} dias em {destino} com foco em: "
            f"{interesses}. Use EXATAMENTE a tabela de custos detalhada "
            f"em {moeda_txt} gerada pelo colega logístico. "
            f"Escreva TODO o roteiro em {language_name(idioma)}."
        )
        if refine_context:
            description += f"\n\n{refine_context}"
        return Task(
            description=description,
            expected_output=(
                "Roteiro Markdown completo com: Título atrativo, Tabela de "
                f"Custos Detalhada em {moeda_txt}, Cronograma de {dias} dias "
                "(manhã/tarde/noite) e dicas exclusivas. "
                f"A moeda deve ser exclusivamente {moeda_txt} e o idioma, "
                f"{language_name(idioma)}."
            ),
            agent=agent,
        )
