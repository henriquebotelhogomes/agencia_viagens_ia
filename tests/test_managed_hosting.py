"""Testes das adaptações exigidas pela hospedagem gerenciada (ADR-0015).

Cobre as duas correções que, sem teste, quebrariam silenciosamente em produção:
a normalização da URL do banco e a configuração de TLS do Redis.
"""

import pytest

from src.config import Settings
from src.services.redis_client import (
    connection_kwargs,
    create_async_client,
    create_client,
)


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Normalização da URL do PostgreSQL
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("provided", "expected"),
    [
        # Formato entregue por Heroku e Render
        (
            "postgres://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        # Formato canônico do PostgreSQL, ainda sem driver async
        (
            "postgresql://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        # Já explícito: não deve ser alterado
        (
            "postgresql+asyncpg://user:pw@host:5432/db",
            "postgresql+asyncpg://user:pw@host:5432/db",
        ),
        # Outros dialetos passam intactos (SQLite é usado nos testes)
        ("sqlite+aiosqlite:///:memory:", "sqlite+aiosqlite:///:memory:"),
        ("", ""),
    ],
)
def test_database_url_normalizada_para_driver_async(
    provided: str, expected: str
) -> None:
    """Sem o driver async explícito, o SQLAlchemy falharia em contexto assíncrono."""
    assert expected == _settings(DATABASE_URL=provided).DATABASE_URL


def test_database_url_ignora_espacos_acidentais() -> None:
    """Colar a URL no dashboard costuma trazer espaços invisíveis."""
    settings = _settings(DATABASE_URL="  postgres://user:pw@host/db  ")

    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pw@host/db"


def test_normalizacao_preserva_senha_com_caracteres_especiais() -> None:
    """A troca do prefixo não deve tocar no resto da URL."""
    url = "postgres://u:p%40ss%3Aword@host:5432/db?sslmode=require"

    normalized = _settings(DATABASE_URL=url).DATABASE_URL

    assert normalized == (
        "postgresql+asyncpg://u:p%40ss%3Aword@host:5432/db?sslmode=require"
    )


# ---------------------------------------------------------------------------
# TLS do Redis gerenciado
# ---------------------------------------------------------------------------
def test_rediss_desabilita_verificacao_de_certificado() -> None:
    """Provedores gerenciados usam certificado self-signed; sem isso, falha."""
    kwargs = connection_kwargs(_settings(REDIS_URL="rediss://host:6379"))

    assert kwargs["ssl_cert_reqs"] is None


def test_redis_sem_tls_nao_recebe_parametro_ssl() -> None:
    """Passar `ssl_cert_reqs` numa conexão não-TLS é erro de configuração."""
    kwargs = connection_kwargs(_settings(REDIS_URL="redis://localhost:6379"))

    assert "ssl_cert_reqs" not in kwargs


def test_timeout_de_conexao_sempre_aplicado() -> None:
    """Sem timeout, um Redis inacessível pendura o arranque."""
    kwargs = connection_kwargs(
        _settings(REDIS_URL="redis://localhost:6379", REDIS_CONNECT_TIMEOUT=7.5)
    )

    assert kwargs["socket_connect_timeout"] == 7.5


def test_extras_do_chamador_sobrepoem_os_padroes() -> None:
    """Cada serviço ajusta o que precisa sem duplicar a base."""
    kwargs = connection_kwargs(
        _settings(REDIS_URL="redis://localhost:6379"),
        decode_responses=True,
        socket_connect_timeout=1.0,
    )

    assert kwargs["decode_responses"] is True
    assert kwargs["socket_connect_timeout"] == 1.0


def test_create_client_repassa_config_de_tls(mocker) -> None:
    """Garante que a fábrica sync realmente aplica os kwargs montados."""
    from_url = mocker.patch("src.services.redis_client.redis.from_url")
    settings = _settings(REDIS_URL="rediss://host:6379")

    create_client(settings, decode_responses=True)

    _, kwargs = from_url.call_args
    assert kwargs["ssl_cert_reqs"] is None
    assert kwargs["decode_responses"] is True


def test_create_async_client_repassa_config_de_tls(mocker) -> None:
    """Mesma garantia para o cliente assíncrono."""
    from_url = mocker.patch("src.services.redis_client.aioredis.from_url")
    settings = _settings(REDIS_URL="rediss://host:6379")

    create_async_client(settings, decode_responses=True)

    _, kwargs = from_url.call_args
    assert kwargs["ssl_cert_reqs"] is None
    assert kwargs["decode_responses"] is True


def test_fabricas_usam_settings_globais_quando_omitidas(mocker) -> None:
    """Chamadas sem argumento devem cair na configuração da aplicação."""
    from_url = mocker.patch("src.services.redis_client.redis.from_url")
    mocker.patch(
        "src.services.redis_client.get_settings",
        return_value=_settings(REDIS_URL="rediss://global:6379"),
    )

    create_client()

    args, kwargs = from_url.call_args
    assert args[0] == "rediss://global:6379"
    assert kwargs["ssl_cert_reqs"] is None


def test_fila_usa_cliente_com_config_de_tls(mocker) -> None:
    """A fila precisa herdar o TLS, senão o worker não conecta em produção."""
    create = mocker.patch(
        "src.services.queue_service.create_async_client",
        return_value=mocker.MagicMock(),
    )
    from src.services.queue_service import build_queue

    build_queue(_settings(REDIS_URL="rediss://host:6379", QUEUE_NAME="voyager"))

    create.assert_called_once()
