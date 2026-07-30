"""Testes das dependências injetáveis e do ciclo de vida da aplicação."""

import pytest
from fastapi import FastAPI, Request

from src.api import deps
from src.api.main import create_app, lifespan
from src.config import Settings
from src.services.rate_limiter import hash_client_ip


def _request(headers: dict[str, str], client_host: str | None) -> Request:
    """Monta um `Request` mínimo para exercitar as dependências."""
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "client": (client_host, 12345) if client_host else None,
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# Identificação do cliente (base do rate limiting)
# ---------------------------------------------------------------------------


def test_client_ip_hash_uses_socket_when_no_proxy() -> None:
    """Sem proxy, usa o IP da conexão."""
    request = _request({}, "203.0.113.10")

    assert deps.client_ip_hash_dep(request) == hash_client_ip("203.0.113.10")


def test_client_ip_hash_prefers_first_forwarded_address() -> None:
    """Atrás de proxy, o cliente original é o primeiro de `X-Forwarded-For`."""
    request = _request(
        {"X-Forwarded-For": "198.51.100.7, 10.0.0.1, 10.0.0.2"}, "10.0.0.2"
    )

    assert deps.client_ip_hash_dep(request) == hash_client_ip("198.51.100.7")


def test_client_ip_hash_handles_missing_client() -> None:
    """Sem cliente identificável, ainda produz um hash estável."""
    request = _request({}, None)

    assert deps.client_ip_hash_dep(request) == hash_client_ip("unknown")


def test_client_ip_never_appears_in_hash() -> None:
    """Garantia de privacidade: o IP não é recuperável do valor armazenado."""
    ip = "203.0.113.99"
    request = _request({}, ip)

    assert ip not in deps.client_ip_hash_dep(request)


# ---------------------------------------------------------------------------
# Dependências simples
# ---------------------------------------------------------------------------


def test_settings_dep_returns_application_settings() -> None:
    """A dependência de configuração devolve a instância do processo."""
    assert isinstance(deps.settings_dep(), Settings)


def test_progress_bus_and_rate_limiter_come_from_app_state(mocker) -> None:
    """Os serviços compartilhados são criados no lifespan, não por request."""
    app = FastAPI()
    app.state.progress_bus = mocker.sentinel.bus
    app.state.rate_limiter = mocker.sentinel.limiter
    request = mocker.MagicMock(app=app)

    assert deps.progress_bus_dep(request) is mocker.sentinel.bus
    assert deps.rate_limiter_dep(request) is mocker.sentinel.limiter


# ---------------------------------------------------------------------------
# Ciclo de vida
# ---------------------------------------------------------------------------


async def test_lifespan_creates_and_closes_shared_services(mocker) -> None:
    """O lifespan monta os serviços na entrada e os libera na saída."""
    mocker.patch("src.api.main.setup_logger")
    mocker.patch("src.api.main.configure_llm_runtime")
    close_queue = mocker.patch("src.api.main.close_queue")
    dispose_engine = mocker.patch("src.api.main.dispose_engine")
    mocker.patch(
        "src.api.main.get_settings",
        return_value=Settings(
            _env_file=None,
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            REDIS_URL="redis://localhost:6379/0",
        ),
    )
    bus = mocker.patch("src.api.main.ProgressBus").return_value
    bus.close = mocker.AsyncMock()
    limiter = mocker.patch("src.api.main.RateLimiter").return_value
    limiter.close = mocker.AsyncMock()

    app = FastAPI()
    async with lifespan(app):
        assert app.state.progress_bus is bus
        assert app.state.rate_limiter is limiter

    bus.close.assert_awaited_once()
    limiter.close.assert_awaited_once()
    close_queue.assert_awaited_once()
    dispose_engine.assert_awaited_once()


async def test_lifespan_skips_engine_dispose_without_database(mocker) -> None:
    """Sem banco configurado, não há pool para liberar."""
    mocker.patch("src.api.main.setup_logger")
    mocker.patch("src.api.main.configure_llm_runtime")
    mocker.patch("src.api.main.close_queue")
    dispose_engine = mocker.patch("src.api.main.dispose_engine")
    mocker.patch("src.api.main.get_settings", return_value=Settings(_env_file=None))
    mocker.patch("src.api.main.ProgressBus").return_value.close = mocker.AsyncMock()
    mocker.patch("src.api.main.RateLimiter").return_value.close = mocker.AsyncMock()

    async with lifespan(FastAPI()):
        pass

    dispose_engine.assert_not_awaited()


# ---------------------------------------------------------------------------
# Montagem do app
# ---------------------------------------------------------------------------


def test_docs_are_exposed_outside_production(mocker) -> None:
    """Em desenvolvimento, as docs interativas ficam disponíveis."""
    mocker.patch("src.api.main.get_settings", return_value=Settings(_env_file=None))

    app = create_app()

    assert app.docs_url == "/docs"


def test_docs_are_disabled_in_production(mocker) -> None:
    """Em produção, `/docs` e `/redoc` são desligados (redução de superfície)."""
    mocker.patch(
        "src.api.main.get_settings",
        return_value=Settings(_env_file=None, APP_ENV="production"),
    )

    app = create_app()

    assert app.docs_url is None
    assert app.redoc_url is None


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        ("", ["http://localhost:3000", "http://localhost:8501"]),
        ("https://app.voyager.ai", ["https://app.voyager.ai"]),
        ("https://a.com, https://b.com", ["https://a.com", "https://b.com"]),
    ],
)
def test_cors_origins_never_use_wildcard(configured: str, expected: list[str]) -> None:
    """CORS é sempre explícito — `*` quebraria o uso de credenciais."""
    settings = Settings(_env_file=None, CORS_ALLOWED_ORIGINS=configured)

    assert settings.cors_origins == expected
    assert "*" not in settings.cors_origins
