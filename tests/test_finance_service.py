import pytest

from src.services.finance_service import FinanceService


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
