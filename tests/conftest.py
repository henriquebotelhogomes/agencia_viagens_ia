# tests/conftest.py
import os
from unittest.mock import MagicMock
import pytest
from dotenv import load_dotenv
from src.config import Settings

# Carrega variáveis de ambiente
load_dotenv()

@pytest.fixture(scope="session")
def mock_settings():
    """Fixture para mockar as configurações do projeto."""
    return Settings(
        GROQ_API_KEY="mock_groq_key",
        SERPER_API_KEY="mock_serper_key",
        GOOGLE_API_KEY="mock_google_key"
    )

@pytest.fixture
def mock_nominatim(mocker):
    """Fixture para mockar o serviço Nominatim da Geopy."""
    mock_geolocator = mocker.patch('src.services.geocoding_service.Nominatim')
    mock_location = MagicMock()
    mock_location.latitude = 12.34
    mock_location.longitude = 56.78
    mock_location.address = "Mocked Address"
    mock_geolocator.return_value.geocode.return_value = mock_location
    return mock_geolocator

@pytest.fixture
def mock_requests_get(mocker):
    """Fixture para mockar chamadas HTTP feitas pela biblioteca requests."""
    mock_get = mocker.patch('requests.get')
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"rates": {"USD": 1.0, "BRL": 5.0}}
    mock_get.return_value = mock_response
    return mock_get