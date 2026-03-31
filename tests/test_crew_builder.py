# tests/test_crew_builder.py
from unittest.mock import MagicMock

import pytest

from src.crew_builder import CrewBuilder


@pytest.mark.parametrize(
    "agent_type", ["local_expert", "logistics_manager", "itinerary_architect"]
)
def test_create_agent(
    mock_settings, mock_chat_groq, mock_crew_agent, mocker, agent_type: str
) -> None:
    """
    Testa a criação de diferentes tipos de agentes.
    Parametrização cobre múltiplos cenários com o mesmo código.
    """
    builder = CrewBuilder(mock_settings)

    with mocker.patch(
        "src.agents.Agent", side_effect=lambda **kwargs: MagicMock(**kwargs)
    ):
        if agent_type == "local_expert":
            agent = builder.create_local_expert_agent()
            expected_role = "Guia Local"
            expected_tools = []  # Sem ferramentas específicas
        elif agent_type == "logistics_manager":
            agent = builder.create_logistics_manager_agent()
            expected_role = "Gerente de Logística"
            expected_tools = ["search_tool"]  # Assumindo Serper
        else:  # itinerary_architect
            agent = builder.create_itinerary_architect_agent()
            expected_role = "Arquiteto de Roteiros"
            expected_tools = []

        assert agent.role == expected_role
    assert agent.llm == mock_chat_groq
    assert len(agent.tools) == len(expected_tools)


def test_build_crew_complete(
    mock_settings, mock_chat_groq, mock_crew_agent, mock_crew_task, mock_crew
) -> None:
    """
    Testa a construção completa da crew com agentes e tarefas.
    Verifica se kickoff é chamado corretamente.
    """
    builder = CrewBuilder(mock_settings)

    # Simula criação de agentes e tarefas
    builder.create_local_expert_agent = MagicMock(
        return_value=mock_crew_agent.return_value
    )
    builder.create_logistics_manager_agent = MagicMock(
        return_value=mock_crew_agent.return_value
    )
    builder.create_itinerary_architect_agent = MagicMock(
        return_value=mock_crew_agent.return_value
    )
    builder.create_research_task = MagicMock(return_value=mock_crew_task.return_value)
    builder.create_logistics_task = MagicMock(return_value=mock_crew_task.return_value)
    builder.create_itinerary_task = MagicMock(return_value=mock_crew_task.return_value)

    crew = builder.build_crew("Paris", 7, "Cultura")

    # Verifica se os agentes e tarefas foram passados corretamente para a Crew
    # Usamos assert_called_once() e depois inspecionamos os argumentos
    # para maior robustez com Pydantic
    mock_crew.assert_called_once()
    args, kwargs = mock_crew.call_args
    assert kwargs["agents"] == [mock_crew_agent.return_value] * 3
    assert kwargs["tasks"] == [mock_crew_task.return_value] * 3
    assert kwargs["verbose"] is True

    # Chama kickoff e verifica
    crew.kickoff()
    mock_crew.return_value.kickoff.assert_called_once()
