import pytest
from unittest.mock import MagicMock
from src.services.geocoding_service import GeocodingService
from src.models.location import Location

@pytest.fixture
def mock_geocoder():
    with MagicMock() as mock:
        yield mock

def test_extract_locations_empty_on_error(mocker):
    # Mock ChatGroq to return a mock instance whose 'invoke' method raises an error
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("API Error")
    mocker.patch("src.services.geocoding_service.ChatGroq", return_value=mock_llm)
    
    service = GeocodingService()
    locations = service.extract_locations("Some itinerary")
    assert locations == []

def test_get_coordinates_returns_none_on_fail(mocker):
    service = GeocodingService()
    # Mock geolocator.geocode to return None
    service.geolocator.geocode = MagicMock(return_value=None)
    
    coords = service.get_coordinates("NonExistentPlace")
    assert coords is None

def test_process_itinerary_locations_full_flow(mocker):
    service = GeocodingService()
    
    # Mock extract_locations
    mocker.patch.object(service, 'extract_locations', return_value=["Paris", "London"])
    
    # Mock get_coordinates
    mock_location = MagicMock()
    mock_location.latitude = 48.8566
    mock_location.longitude = 2.3522
    
    service.geolocator.geocode = MagicMock(return_value=mock_location)
    
    results = service.process_itinerary_locations("Dummy text")
    
    assert len(results) == 2
    assert isinstance(results[0], Location)
    assert results[0].name == "Paris"
    assert results[0].lat == 48.8566
