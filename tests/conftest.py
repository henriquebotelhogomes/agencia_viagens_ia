from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture  # Import adicionado para type hints do mocker

from src.config import Settings

# Variáveis sensíveis que NUNCA podem vazar do .env real para os testes
# (padrão §8.1 do PRD: "sem chave real em teste, nunca").
_SENSITIVE_ENV_VARS = (
    "OPENCODE_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "GEOAPIFY_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_HEADERS",
    "GROQ_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "SERPER_API_KEY",
    "REDIS_URL",
    "DATABASE_URL",
)


@pytest.fixture(autouse=True)
def isolate_secrets_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove chaves reais do ambiente antes de cada teste.

    O CrewAI executa ``load_dotenv()`` no próprio import, contaminando
    ``os.environ`` com o `.env` local — sem este fixture, um `Settings`
    construído dentro do teste captaria chaves reais e faria chamadas de
    rede verdadeiras (regressão detectada em 2026-07-29).
    """
    for var in _SENSITIVE_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture(scope="session")
def mock_settings() -> Settings:
    """
    Fixture para mockar as configurações do projeto.
    Retorna uma instância de Settings com chaves mockadas, garantindo isolamento.
    Uso: Evita dependência de .env real em testes.
    """
    return Settings(
        _env_file=None,
        # Novos provedores (PRD D2, D10, D11, D12)
        OPENCODE_API_KEY="mock_opencode_key",
        OPENROUTER_API_KEY="mock_openrouter_key",
        TAVILY_API_KEY="mock_tavily_key",
        GEOAPIFY_API_KEY="mock_geoapify_key",
        LANGFUSE_PUBLIC_KEY="mock_langfuse_public_key",
        LANGFUSE_SECRET_KEY="mock_langfuse_secret_key",
        # Legado (playground Streamlit)
        GROQ_API_KEY="mock_groq_key",
        SERPER_API_KEY="mock_serper_key",
        GOOGLE_API_KEY="mock_google_key",
    )


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
