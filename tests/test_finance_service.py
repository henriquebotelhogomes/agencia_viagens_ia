import pytest
from src.services.finance_service import FinanceService

def test_estimate_costs_logic():
    service = FinanceService()
    logs = "A extremely long log message that repeats itself " * 100
    
    results = service.estimate_costs(logs)
    
    assert "total_tokens" in results
    assert "custo_gpt4o" in results
    assert "custo_groq" in results
    assert results["custo_gpt4o"] > results["custo_groq"]
    assert results["savings"] > 0

def test_estimate_costs_empty_logs():
    service = FinanceService()
    results = service.estimate_costs("")
    
    assert results["total_tokens"] >= 2500 # Base tokens
    assert results["custo_groq"] > 0
