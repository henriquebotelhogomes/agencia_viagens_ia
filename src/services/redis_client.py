"""Fábrica de clientes Redis (ADR-0015).

Centraliza a construção de conexões para que a configuração de rede e TLS viva
num único lugar. Antes, cinco módulos repetiam os mesmos parâmetros — e cada um
teria de ser corrigido separadamente ao mudar de provedor.

O caso que motivou a centralização: provedores gerenciados (Heroku Key-Value
Store, entre outros) expõem a instância via ``rediss://`` com **certificado
self-signed**. O ``redis-py`` valida o certificado por padrão e a conexão falha
com ``SSLCertVerificationError``. Como o tráfego é interno e a alternativa seria
não ter TLS nenhum, desabilitamos apenas a *verificação da cadeia*, mantendo o
transporte cifrado.
"""

from typing import Any

import redis
import redis.asyncio as aioredis

from src.config import Settings, get_settings


def connection_kwargs(settings: Settings | None = None, **extra: Any) -> dict[str, Any]:
    """Monta os parâmetros de conexão comuns a todos os clientes.

    Args:
        settings: configuração a usar (injeta em testes).
        **extra: parâmetros específicos do chamador (ex.: ``decode_responses``).

    Returns:
        Dicionário de ``kwargs`` pronto para ``from_url``.
    """
    resolved = settings or get_settings()
    kwargs: dict[str, Any] = {
        "socket_connect_timeout": resolved.REDIS_CONNECT_TIMEOUT,
    }
    if resolved.REDIS_URL.startswith("rediss://"):
        # Certificado self-signed: cifra o tráfego sem exigir cadeia confiável
        kwargs["ssl_cert_reqs"] = None
    kwargs.update(extra)
    return kwargs


def create_client(settings: Settings | None = None, **extra: Any) -> redis.Redis:
    """Cria um cliente Redis síncrono."""
    resolved = settings or get_settings()
    return redis.from_url(resolved.REDIS_URL, **connection_kwargs(resolved, **extra))


def create_async_client(
    settings: Settings | None = None, **extra: Any
) -> aioredis.Redis:
    """Cria um cliente Redis assíncrono."""
    resolved = settings or get_settings()
    return aioredis.from_url(resolved.REDIS_URL, **connection_kwargs(resolved, **extra))
