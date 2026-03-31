# tests/test_finance_service.py
import pytest
from src.services.finance_service import FinanceService

def test_get_exchange_rate_success(mock_requests_get):
    """Testa a obtenção bem-sucedida de uma taxa de câmbio."""
    service = FinanceService()
    rate = service.get_exchange_rate("USD", "BRL")
    assert rate == 5.0

def test_get_exchange_rate_invalid_currency(mock_requests_get):
    """Testa o cenário onde uma moeda inválida é fornecida."""
    service = FinanceService()
    rate = service.get_exchange_rate("USD", "XYZ")
    assert rate is None