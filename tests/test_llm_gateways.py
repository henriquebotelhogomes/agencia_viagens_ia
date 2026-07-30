"""Testes da estratégia de gateways de LLM e do failover (PRD D2)."""

from unittest.mock import MagicMock

import pytest

from src.agents import GO_PRO_MODEL, TravelAgents
from src.config import Settings
from src.crew_builder import CrewBuilder


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


@pytest.fixture
def captured_llm(mocker):
    """Captura os kwargs passados ao construtor ``LLM`` do CrewAI."""
    return mocker.patch("src.agents.LLM")


# ---------------------------------------------------------------------------
# Roteamento de tiers por gateway
# ---------------------------------------------------------------------------


def test_primary_tiers_use_opencode_go(captured_llm) -> None:
    """Sem failover, `fast` e `fast-tools` vão para o OpenCode Go."""
    settings = _settings(OPENCODE_API_KEY="go_key", OPENROUTER_API_KEY="or_key")
    agents = TravelAgents(settings)

    _ = agents.llm_fast
    kwargs = captured_llm.call_args.kwargs
    assert kwargs["model"] == f"openai/{settings.LLM_MODEL_FAST}"
    assert kwargs["api_base"] == settings.OPENCODE_API_BASE

    _ = agents.llm_fast_tools
    kwargs = captured_llm.call_args.kwargs
    assert kwargs["model"] == f"openai/{settings.LLM_MODEL_FAST_TOOLS}"


def test_pro_tier_uses_openrouter(captured_llm) -> None:
    """O tier `pro` roda no OpenRouter (qualidade consistente)."""
    settings = _settings(OPENCODE_API_KEY="go_key", OPENROUTER_API_KEY="or_key")
    agents = TravelAgents(settings)

    _ = agents.llm_pro

    kwargs = captured_llm.call_args.kwargs
    assert kwargs["model"] == settings.LLM_MODEL_PRO
    assert "api_base" not in kwargs


def test_fallback_mode_routes_everything_to_openrouter(captured_llm) -> None:
    """Com `use_fallback`, os tiers baratos migram para o OpenRouter."""
    settings = _settings(OPENCODE_API_KEY="go_key", OPENROUTER_API_KEY="or_key")
    agents = TravelAgents(settings, use_fallback=True)

    _ = agents.llm_fast
    assert captured_llm.call_args.kwargs["model"] == settings.LLM_FALLBACK_FAST

    _ = agents.llm_fast_tools
    assert captured_llm.call_args.kwargs["model"] == settings.LLM_FALLBACK_TOOLS

    # No failover, o `pro` usa o Go como reserva
    _ = agents.llm_pro
    assert captured_llm.call_args.kwargs["model"] == f"openai/{GO_PRO_MODEL}"


def test_without_opencode_key_falls_back_automatically(captured_llm) -> None:
    """Sem chave do Go, o OpenRouter é o único caminho (degradação graciosa)."""
    settings = _settings(OPENROUTER_API_KEY="or_key")
    agents = TravelAgents(settings)

    assert agents.use_fallback is True
    _ = agents.llm_fast
    assert captured_llm.call_args.kwargs["model"] == settings.LLM_FALLBACK_FAST


def test_llms_are_memoized_per_instance(captured_llm) -> None:
    """Cada tier é construído uma única vez por instância."""
    agents = TravelAgents(_settings(OPENCODE_API_KEY="go_key"))

    first = agents.llm_fast
    second = agents.llm_fast

    assert first is second
    assert captured_llm.call_count == 1


# ---------------------------------------------------------------------------
# Failover orquestrado pelo CrewBuilder
# ---------------------------------------------------------------------------


def test_run_retries_on_openrouter_when_primary_fails(mocker) -> None:
    """Falha no gateway primário dispara uma nova execução no fallback."""
    mocker.patch("src.agents.LLM")
    failing_crew = MagicMock()
    failing_crew.kickoff.side_effect = Exception("429 budget exceeded")
    ok_crew = MagicMock()
    ok_crew.kickoff.return_value = "roteiro do fallback"
    build = mocker.patch.object(
        CrewBuilder, "build_crew", side_effect=[failing_crew, ok_crew]
    )

    builder = CrewBuilder(
        _settings(OPENCODE_API_KEY="go_key", OPENROUTER_API_KEY="or_key"),
        destino="Paris",
        dias=3,
        origem="SP",
        interesses="museus",
    )
    result = builder.run()

    assert result == "roteiro do fallback"
    assert build.call_count == 2


def test_run_does_not_retry_twice_in_fallback_mode(mocker) -> None:
    """Já no fallback, a falha propaga em vez de gerar loop."""
    mocker.patch("src.agents.LLM")
    failing_crew = MagicMock()
    failing_crew.kickoff.side_effect = Exception("provider down")
    mocker.patch.object(CrewBuilder, "build_crew", return_value=failing_crew)

    builder = CrewBuilder(
        _settings(OPENROUTER_API_KEY="or_key"),
        destino="Paris",
        dias=3,
        use_fallback=True,
    )

    with pytest.raises(Exception, match="provider down"):
        builder.run()


def test_run_returns_primary_result_without_failover(mocker) -> None:
    """Caminho feliz: nenhuma reconstrução de crew."""
    mocker.patch("src.agents.LLM")
    crew = MagicMock()
    crew.kickoff.return_value = "roteiro do primario"
    build = mocker.patch.object(CrewBuilder, "build_crew", return_value=crew)

    builder = CrewBuilder(_settings(OPENCODE_API_KEY="go_key"), destino="Roma", dias=2)

    assert builder.run() == "roteiro do primario"
    assert build.call_count == 1
