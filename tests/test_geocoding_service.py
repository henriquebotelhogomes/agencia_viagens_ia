"""Testes do GeocodingService: extração via tier `fast`, Geoapify e cache."""

import json
from unittest.mock import MagicMock

from src.config import Settings
from src.models.location import Location
from src.services.cache_service import CacheService
from src.services.geocoding_service import MAX_EXTRACTED_LOCATIONS, GeocodingService


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def _service_with_llm(mocker, content: str | Exception) -> GeocodingService:
    """Serviço com Go configurado e litellm.completion mockado."""
    mock_completion = mocker.patch("src.services.geocoding_service.litellm.completion")
    if isinstance(content, Exception):
        mock_completion.side_effect = content
    else:
        response = MagicMock()
        response.choices[0].message.content = content
        mock_completion.return_value = response
    service = GeocodingService(_settings(OPENCODE_API_KEY="mock_go_key"))
    return service


# ---------------------------------------------------------------------------
# Extração de locais (tier `fast` via litellm, schema LocationList — S16)
# ---------------------------------------------------------------------------


def test_extract_locations_parses_valid_json(mocker) -> None:
    payload = json.dumps(
        {"locations": [{"name": "Museu do Louvre"}, {"name": "  Torre Eiffel  "}]}
    )
    service = _service_with_llm(mocker, payload)

    names = service.extract_locations("Roteiro de Paris")

    assert names == ["Museu do Louvre", "Torre Eiffel"]


def test_extract_locations_caps_at_maximum(mocker) -> None:
    payload = json.dumps({"locations": [{"name": f"Local {i}"} for i in range(10)]})
    service = _service_with_llm(mocker, payload)

    assert len(service.extract_locations("Roteiro extenso")) == MAX_EXTRACTED_LOCATIONS


def test_extract_locations_empty_on_llm_error(mocker) -> None:
    """Toda a cadeia falhando resulta em lista vazia, sem exceção."""
    service = _service_with_llm(mocker, Exception("API Error"))

    assert service.extract_locations("Some itinerary") == []


def test_extract_locations_empty_on_invalid_json(mocker) -> None:
    service = _service_with_llm(mocker, "desculpe, não consigo ajudar")

    assert service.extract_locations("Roteiro") == []


def test_extract_locations_empty_input_short_circuits(mocker) -> None:
    mock_completion = mocker.patch("src.services.geocoding_service.litellm.completion")
    service = GeocodingService(_settings(OPENCODE_API_KEY="mock_go_key"))

    assert service.extract_locations("") == []
    mock_completion.assert_not_called()


def test_extraction_chain_falls_back_to_openrouter(mocker) -> None:
    """Se o Go falhar, a extração tenta o fallback do OpenRouter (D2)."""
    mock_completion = mocker.patch("src.services.geocoding_service.litellm.completion")
    ok_response = MagicMock()
    ok_response.choices[0].message.content = json.dumps(
        {"locations": [{"name": "Coliseu"}]}
    )
    mock_completion.side_effect = [Exception("Go 429"), ok_response]

    service = GeocodingService(
        _settings(OPENCODE_API_KEY="mock_go", OPENROUTER_API_KEY="mock_or")
    )
    names = service.extract_locations("Roteiro de Roma")

    assert names == ["Coliseu"]
    assert mock_completion.call_count == 2
    # Primeira tentativa no Go, segunda no OpenRouter
    first, second = mock_completion.call_args_list
    assert first.kwargs["model"].startswith("openai/")
    assert second.kwargs["model"].startswith("openrouter/")


# ---------------------------------------------------------------------------
# Geocoding: Geoapify primário (D10), Nominatim fallback, cache Redis
# ---------------------------------------------------------------------------


def test_get_coordinates_uses_geoapify_when_key_present(mocker) -> None:
    mock_get = mocker.patch("src.services.geocoding_service.requests.get")
    mock_get.return_value.json.return_value = {
        "features": [{"geometry": {"coordinates": [2.3522, 48.8566]}}]
    }
    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"))

    coords = service.get_coordinates("Paris")

    # Geoapify devolve [lon, lat]; o serviço normaliza para (lat, lon)
    assert coords == (48.8566, 2.3522)
    assert mock_get.call_args.kwargs["params"]["text"] == "Paris"


def test_get_coordinates_geoapify_error_returns_none(mocker) -> None:
    mocker.patch(
        "src.services.geocoding_service.requests.get",
        side_effect=Exception("timeout"),
    )
    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"))

    assert service.get_coordinates("Paris") is None


def test_get_coordinates_falls_back_to_nominatim_without_key() -> None:
    """Sem chave Geoapify, degrada graciosamente para o Nominatim."""
    service = GeocodingService(_settings(geocoding_delay=0.0))
    mock_location = MagicMock(latitude=12.34, longitude=56.78)
    service._geolocator = MagicMock()
    service._geolocator.geocode.return_value = mock_location

    assert service.get_coordinates("Lisboa") == (12.34, 56.78)


def test_get_coordinates_empty_address_returns_none() -> None:
    service = GeocodingService(_settings())

    assert service.get_coordinates("") is None


def test_get_coordinates_reads_from_cache_before_network(mocker) -> None:
    """Cache hit não toca a rede (D10: hit ratio > 80% esperado)."""
    mock_get = mocker.patch("src.services.geocoding_service.requests.get")
    cache = CacheService(_settings())
    cache.enabled = True
    cache.client = MagicMock()
    cache.client.get.return_value = json.dumps([48.85, 2.35])

    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"), cache=cache)

    assert service.get_coordinates("Paris") == (48.85, 2.35)
    mock_get.assert_not_called()


def test_get_coordinates_saves_to_cache_after_geocoding(mocker) -> None:
    mock_get = mocker.patch("src.services.geocoding_service.requests.get")
    mock_get.return_value.json.return_value = {
        "features": [{"geometry": {"coordinates": [2.35, 48.85]}}]
    }
    settings = _settings(
        GEOAPIFY_API_KEY="mock_geo_key", GEOCODING_CACHE_TTL_SECONDS=999
    )
    cache = CacheService(_settings())
    cache.enabled = True
    cache.client = MagicMock()
    cache.client.get.return_value = None

    service = GeocodingService(settings, cache=cache)
    service.get_coordinates("Paris")

    key, ttl, value = cache.client.setex.call_args[0]
    assert key.startswith("geocode:")
    assert ttl == 999
    assert json.loads(value) == [48.85, 2.35]


def test_process_itinerary_locations_full_flow(mocker) -> None:
    """Fluxo completo: extração + geocodificação."""
    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"))
    mocker.patch.object(service, "extract_locations", return_value=["Paris", "London"])
    mocker.patch.object(
        service,
        "get_coordinates",
        side_effect=[(48.8566, 2.3522), (51.5074, -0.1278)],
    )

    results = service.process_itinerary_locations("Dummy text")

    assert len(results) == 2
    assert isinstance(results[0], Location)
    assert results[0].name == "Paris"
    assert results[0].lat == 48.8566
    assert results[1].name == "London"
    assert results[1].lat == 51.5074


# ---------------------------------------------------------------------------
# Desambiguacao pelo destino (regressao de produto, 2026-07-31)
# ---------------------------------------------------------------------------
def test_busca_inclui_o_destino_como_contexto() -> None:
    """Sem contexto, "Time Out Market" resolvia para Nova York."""
    service = GeocodingService(_settings())

    assert (
        service._search_text("Time Out Market", "Porto, Portugal")
        == "Time Out Market, Porto, Portugal"
    )


def test_busca_nao_repete_o_destino_quando_ja_presente() -> None:
    """Evita "Porto, Portugal, Porto, Portugal" na query."""
    service = GeocodingService(_settings())

    assert (
        service._search_text("Ribeira, Porto, Portugal", "Porto, Portugal")
        == "Ribeira, Porto, Portugal"
    )


def test_busca_sem_contexto_usa_apenas_o_nome() -> None:
    service = GeocodingService(_settings())

    assert service._search_text("Torre Eiffel") == "Torre Eiffel"


def test_cache_separa_o_mesmo_nome_em_destinos_diferentes() -> None:
    """Um "Mercado Central" em Lisboa nao pode servir coordenadas de Madri."""
    service = GeocodingService(_settings())

    lisboa = service._cache_key("Mercado Central", "Lisboa, Portugal")
    madri = service._cache_key("Mercado Central", "Madri, Espanha")

    assert lisboa != madri


def test_geocoding_recebe_query_com_contexto(mocker) -> None:
    """O contexto precisa chegar ao provedor, nao parar no meio do caminho."""
    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"))
    geoapify = mocker.patch.object(
        service, "_geocode_geoapify", return_value=(41.15, -8.61)
    )

    service.get_coordinates("Mercado do Bolhao", "Porto, Portugal")

    geoapify.assert_called_once_with("Mercado do Bolhao, Porto, Portugal")


def test_process_itinerary_locations_propaga_o_contexto(mocker) -> None:
    service = GeocodingService(_settings(GEOAPIFY_API_KEY="mock_geo_key"))
    mocker.patch.object(service, "extract_locations", return_value=["Ribeira"])
    coords = mocker.patch.object(
        service, "get_coordinates", return_value=(41.14, -8.61)
    )

    service.process_itinerary_locations("texto", "Porto, Portugal")

    coords.assert_called_once_with("Ribeira", "Porto, Portugal")
