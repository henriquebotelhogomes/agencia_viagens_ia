# tests/test_crew_builder.py
import pytest
from src.crew_builder import CrewBuilder

def test_create_local_expert_agent(mock_settings):
    """Testa a criação do agente Local Expert."""
    builder = CrewBuilder(mock_settings)
    agent = builder.create_local_expert_agent()
    assert agent.role == "Guia Local"