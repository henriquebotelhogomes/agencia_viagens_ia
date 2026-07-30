import pytest
import requests

from src.services.finance_service import EXCHANGE_RATE_API_URL, FinanceService


@pytest.mark.parametrize(
    "log_length, expected_tokens",
    [
        (100, 500),  # Logs curtos
        (1000, 2000),  # Logs médios
        (10000, 8000),  # Logs longos
    ],
)
def test_estimate_costs_logic(log_length: int, expected_tokens: int) -> None:
    """
    Testa a estimativa de custos para diferentes comprimentos de logs.
    Parametrização cobre múltiplos cenários.
    """
    service = FinanceService()
    logs = "A" * log_length  # Logs simples para teste

    results = service.estimate_costs(logs)

    assert "total_tokens" in results
    assert results["total_tokens"] >= expected_tokens
    assert "custo_gpt4o" in results
    assert "custo_groq" in results
    assert results["custo_gpt4o"] > results["custo_groq"]
    assert results["savings"] > 0, "Economia deve ser positiva"


def test_estimate_costs_empty_logs() -> None:
    """Testa estimativa com logs vazios (tokens mínimos)."""
    service = FinanceService()
    results = service.estimate_costs("")

    assert results["total_tokens"] >= 2500  # Tokens base
    assert results["custo_groq"] > 0
    assert "savings" in results


def test_estimate_costs_invalid_logs() -> None:
    """Testa com logs inválidos (ex: None)."""
    service = FinanceService()
    with pytest.raises(TypeError, match="Logs must be string"):
        service.estimate_costs(None)


def test_estimate_costs_from_usage_uses_real_tokens() -> None:
    """FinOps real (S4): custos calculados de tokens medidos, não estimados."""
    service = FinanceService()

    stats = service.estimate_costs_from_usage(
        prompt_tokens=800_000, completion_tokens=200_000
    )

    assert stats["total_tokens"] == 1_000_000.0
    # GPT-4o: 0.8M * $5 + 0.2M * $15 = $7.00
    assert stats["custo_gpt4o"] == pytest.approx(7.0)
    # Stack: 0.8M * $0.59 + 0.2M * $0.79 = $0.63
    assert stats["custo_groq"] == pytest.approx(0.63)
    assert stats["savings"] == pytest.approx(6.37)


def test_estimate_costs_from_usage_zero_tokens() -> None:
    """Execução sem tokens (ex.: falha total) não quebra o painel."""
    service = FinanceService()

    stats = service.estimate_costs_from_usage(prompt_tokens=0, completion_tokens=0)

    assert stats["total_tokens"] == 0.0
    assert stats["savings"] == 0.0


# ---------------------------------------------------------------------------
# Câmbio via frankfurter.app (item S5 do PRD)
# ---------------------------------------------------------------------------


def test_get_exchange_rate_success(mock_requests_get) -> None:
    """Retorna a taxa quando a API responde com sucesso."""
    service = FinanceService()

    rate = service.get_exchange_rate("USD", "BRL")

    assert rate == 5.0
    # Verifica endpoint e parâmetros da chamada
    args, kwargs = mock_requests_get.call_args
    assert args[0] == EXCHANGE_RATE_API_URL
    assert kwargs["params"] == {"base": "USD", "symbols": "BRL"}
    assert kwargs["timeout"] > 0


def test_get_exchange_rate_normalizes_input(mock_requests_get) -> None:
    """Moedas em minúsculo/com espaços são normalizadas."""
    service = FinanceService()

    rate = service.get_exchange_rate(" usd ", "brl")

    assert rate == 5.0
    _, kwargs = mock_requests_get.call_args
    assert kwargs["params"] == {"base": "USD", "symbols": "BRL"}


def test_get_exchange_rate_same_currency_short_circuits(mock_requests_get) -> None:
    """Mesma moeda retorna 1.0 sem chamada de rede."""
    service = FinanceService()

    assert service.get_exchange_rate("BRL", "BRL") == 1.0
    mock_requests_get.assert_not_called()


def test_get_exchange_rate_returns_none_on_missing_rate(mock_requests_get) -> None:
    """Taxa ausente na resposta retorna None (sem exceção)."""
    mock_requests_get.return_value.json.return_value = {"rates": {}}
    service = FinanceService()

    assert service.get_exchange_rate("USD", "XYZ") is None


def test_get_exchange_rate_returns_none_on_timeout(mocker) -> None:
    """Timeout de rede retorna None (sem exceção)."""
    mocker.patch(
        "src.services.finance_service.requests.get",
        side_effect=requests.Timeout("timed out"),
    )
    service = FinanceService()

    assert service.get_exchange_rate("USD", "BRL") is None


def test_get_exchange_rate_returns_none_on_http_error(mocker) -> None:
    """Erro HTTP (ex.: 500) retorna None (sem exceção)."""
    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("500")
    mocker.patch(
        "src.services.finance_service.requests.get", return_value=mock_response
    )
    service = FinanceService()

    assert service.get_exchange_rate("USD", "BRL") is None


def test_get_exchange_rate_empty_currency_returns_none(mock_requests_get) -> None:
    """Moeda vazia retorna None sem chamada de rede."""
    service = FinanceService()

    assert service.get_exchange_rate("", "BRL") is None
    mock_requests_get.assert_not_called()
