# tests/test_geocoding_service.py
import pytest
from src.services.geocoding_service import GeocodingService

def test_get_coordinates_success(mock_nominatim):
    """Testa se get_coordinates retorna as coordenadas corretas para um endereço válido."""
    service = GeocodingService()
    address = "New York, USA"
    lat, lon = service.get_coordinates(address)
    assert lat == 12.34
    assert lon == 56.78

def test_get_coordinates_not_found(mock_nominatim):
    """Testa se get_coordinates retorna None para um endereço não encontrado."""
    service = GeocodingService()
    address = "NonExistentAddress"
    mock_nominatim.return_value.geocode.return_value = None
    coords = service.get_coordinates(address)
    assert coords is None