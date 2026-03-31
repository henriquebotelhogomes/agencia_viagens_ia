from unittest.mock import MagicMock

from src.models.location import Location
from src.services.geocoding_service import GeocodingService


def test_extract_locations_empty_on_error(mocker) -> None:
    """Testa extração de locais com erro de LLM (retorna lista vazia)."""
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("API Error")
    mocker.patch("src.services.geocoding_service.ChatGroq", return_value=mock_llm)

    service = GeocodingService()
    locations = service.extract_locations("Some itinerary")

    assert locations == [], "Expected empty list on API error"
    # Verifica se LLM foi chamado
    mock_llm.invoke.assert_called_once()


def test_get_coordinates_returns_none_on_fail(mocker) -> None:
    """Testa coordenadas None para local não encontrado."""
    service = GeocodingService()
    service.geolocator.geocode = MagicMock(return_value=None)

    coords = service.get_coordinates("NonExistentPlace")

    assert coords is None, "Expected None for non-existent place"
    service.geolocator.geocode.assert_called_once_with("NonExistentPlace")


def test_process_itinerary_locations_full_flow(mocker) -> None:
    """Testa fluxo completo: extração + geocodificação."""
    service = GeocodingService()

    # Mock extract_locations
    mocker.patch.object(service, "extract_locations", return_value=["Paris", "London"])

    # Mock geocode with side_effect
    mock_location_paris = MagicMock()
    mock_location_paris.latitude = 48.8566
    mock_location_paris.longitude = 2.3522
    mock_location_london = MagicMock()
    mock_location_london.latitude = 51.5074
    mock_location_london.longitude = -0.1278

    mocker.patch.object(
        service.geolocator,
        "geocode",
        side_effect=[mock_location_paris, mock_location_london],
    )

    results = service.process_itinerary_locations("Dummy text")

    assert len(results) == 2, "Expected 2 locations processed"
    assert isinstance(results[0], Location)
    assert results[0].name == "Paris"
    assert results[0].lat == 48.8566
    assert results[1].name == "London"
    assert results[1].lat == 51.5074


def test_extract_locations_empty_input() -> None:
    """Testa extração com entrada vazia."""
    service = GeocodingService()
    locations = service.extract_locations("")

    assert locations == [], "Expected empty list for empty input"


def test_get_coordinates_empty_address() -> None:
    """Testa coordenadas para endereço vazio."""
    service = GeocodingService()
    coords = service.get_coordinates("")

    assert coords is None, "Expected None for empty address"
