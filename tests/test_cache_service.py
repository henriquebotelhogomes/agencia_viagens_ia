"""Testes do cache de roteiros e da sua degradação graciosa."""

from src.config import Settings
from src.services.cache_service import CacheService, get_cache_service


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_cache_disabled_without_redis_url() -> None:
    """Sem ``REDIS_URL``, o cache fica desativado e não tenta conectar."""
    service = CacheService(_settings())

    assert service.enabled is False
    assert service.client is None


def test_cache_disabled_when_redis_unreachable(mocker) -> None:
    """Redis inacessível desativa o cache sem propagar exceção."""
    mock_client = mocker.MagicMock()
    mock_client.ping.side_effect = Exception("Connection refused")
    mocker.patch("src.services.cache_service.redis.from_url", return_value=mock_client)

    service = CacheService(_settings(REDIS_URL="redis://invalid-host:6379/0"))

    assert service.enabled is False
    assert service.client is None


def test_operations_are_noops_when_disabled() -> None:
    """Leitura retorna ``None`` e escrita não falha com o cache desativado."""
    service = CacheService(_settings())

    assert service.get_cached_itinerary("SP", "Paris", 5, "museus") is None
    service.save_itinerary("SP", "Paris", 5, "museus", "conteúdo")


def test_key_is_deterministic_and_normalized() -> None:
    """A chave ignora caixa e espaços, garantindo hit para buscas equivalentes."""
    service = CacheService(_settings())

    key_a = service._generate_key("São Paulo", "Paris", 5, "Museus")
    key_b = service._generate_key("  são paulo ", " paris", 5, " museus ")
    key_other = service._generate_key("São Paulo", "Paris", 6, "Museus")

    assert key_a == key_b
    assert key_a != key_other
    assert key_a.startswith("itinerary:")


def test_key_includes_currency_and_language() -> None:
    """Moeda/idioma diferentes geram chaves diferentes (item S14 do PRD)."""
    service = CacheService(_settings())

    key_default = service._generate_key("SP", "Paris", 5, "museus")
    key_usd = service._generate_key("SP", "Paris", 5, "museus", moeda="USD")
    key_en = service._generate_key("SP", "Paris", 5, "museus", idioma="en-US")

    assert key_default != key_usd
    assert key_default != key_en
    assert key_usd != key_en
    # Default explícito equivale ao implícito
    assert key_default == service._generate_key(
        "SP", "Paris", 5, "museus", moeda="BRL", idioma="pt-BR"
    )


def test_save_and_get_with_working_redis(mocker) -> None:
    """Com Redis operacional, o roteiro é gravado com TTL e recuperado."""
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = "roteiro em cache"
    mocker.patch("src.services.cache_service.redis.from_url", return_value=mock_client)

    settings = _settings(REDIS_URL="redis://localhost:6379/0", CACHE_TTL_SECONDS=120)
    service = CacheService(settings)
    assert service.enabled is True

    service.save_itinerary("SP", "Paris", 5, "museus", "roteiro")
    key, ttl, content = mock_client.setex.call_args[0]
    assert ttl == 120
    assert content == "roteiro"

    assert (
        service.get_cached_itinerary("SP", "Paris", 5, "museus") == "roteiro em cache"
    )
    mock_client.get.assert_called_once_with(key)


def test_read_error_is_swallowed(mocker) -> None:
    """Erro de leitura no Redis não quebra o fluxo da aplicação."""
    mock_client = mocker.MagicMock()
    mock_client.get.side_effect = Exception("timeout")
    mocker.patch("src.services.cache_service.redis.from_url", return_value=mock_client)

    service = CacheService(_settings(REDIS_URL="redis://localhost:6379/0"))

    assert service.get_cached_itinerary("SP", "Paris", 5, "museus") is None


def test_get_cache_service_is_memoized() -> None:
    """A factory devolve sempre a mesma instância."""
    get_cache_service.cache_clear()
    assert get_cache_service() is get_cache_service()
    get_cache_service.cache_clear()
