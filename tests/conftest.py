from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv
from pytest_mock import MockerFixture  # Import adicionado para type hints do mocker

from src.config import Settings

# Carrega variáveis de ambiente (apenas para testes locais; em CI, usar mocks)
load_dotenv()


@pytest.fixture(scope="session")
def mock_settings() -> Settings:
    """
    Fixture para mockar as configurações do projeto.
    Retorna uma instância de Settings com chaves mockadas, garantindo isolamento.
    Uso: Evita dependência de .env real em testes.
    """
    return Settings(
        GROQ_API_KEY="mock_groq_key",
        SERPER_API_KEY="mock_serper_key",
        GOOGLE_API_KEY="mock_google_key",
    )


@pytest.fixture
def mock_nominatim(mocker: MockerFixture) -> MagicMock:
    """
    Fixture para mockar o serviço Nominatim da Geopy.
    Retorna um mock com localização padrão para sucesso;
    configure side_effect para erros.
    Uso: Isola testes de chamadas de rede reais.
    """
    mock_geolocator = mocker.patch("src.services.geocoding_service.Nominatim")
    mock_location = MagicMock()
    mock_location.latitude = 12.34
    mock_location.longitude = 56.78
    mock_location.address = "Mocked Address"
    mock_geolocator.return_value.geocode.return_value = mock_location
    return mock_geolocator


@pytest.fixture
def mock_requests_get(mocker: MockerFixture) -> MagicMock:
    """
    Fixture para mockar chamadas HTTP com requests.get.
    Retorna resposta 200 com JSON padrão para taxas de câmbio.
    Uso: Testa serviços que dependem de APIs externas sem chamadas reais.
    """
    mock_get = mocker.patch("requests.get")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 1.0, "BRL": 5.0}}
    mock_get.return_value = mock_response
    return mock_get


# Fixtures para CrewAI (com autospec para satisfazer validação Pydantic)
@pytest.fixture
def mock_chat_groq(mocker: MockerFixture) -> MagicMock:
    """Mock do LLM principal (usado em Agents)."""
    mock_llm_class = mocker.patch("src.agents.LLM")
    mock_instance = mock_llm_class.return_value
    mock_instance.invoke.return_value = MagicMock(content="Mocked LLM response")
    return mock_instance


@pytest.fixture
def mock_crew_agent(mocker: MockerFixture) -> MagicMock:
    """Mock do Agent da CrewAI."""
    mock_agent_class = mocker.patch("src.agents.Agent")
    mock_instance = mock_agent_class.return_value
    mock_instance.role = "Mock Role"
    mock_instance.goal = "Mock Goal"
    mock_instance.tools = []
    mock_instance.llm = MagicMock()
    return mock_agent_class


@pytest.fixture
def mock_crew_task(mocker: MockerFixture) -> MagicMock:
    """Mock da Task da CrewAI."""
    mock_task_class = mocker.patch("src.tasks.Task")
    mock_instance = mock_task_class.return_value
    mock_instance.description = "Mock Task"
    mock_instance.agent = MagicMock()
    return mock_task_class


@pytest.fixture
def mock_crew(mocker: MockerFixture) -> MagicMock:
    """Mock da Crew da CrewAI."""
    # Patcheia no src.crew_builder onde é importado
    mock_crew_class = mocker.patch("src.crew_builder.Crew", autospec=True)
    mock_instance = mock_crew_class.return_value
    mock_instance.kickoff.return_value = "Mocked crew result"
    return mock_crew_class
