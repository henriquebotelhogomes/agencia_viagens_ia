"""Rate limiting por IP sobre Redis (FR-09 / ADR-0004).

Enquanto não há autenticação, este é o principal freio contra abuso da demo
pública. Usa janela fixa horária: simples, previsível e suficiente para o caso.

Nota de privacidade: o IP nunca é armazenado em claro — apenas seu hash.
"""

import hashlib
from contextlib import suppress
from dataclasses import dataclass

import redis.asyncio as aioredis
from loguru import logger

from src.config import Settings, get_settings

RATE_LIMIT_PREFIX = "ratelimit:executions"
WINDOW_SECONDS = 3600  # janela de 1 hora


@dataclass(frozen=True)
class RateLimitResult:
    """Resultado de uma verificação de cota."""

    allowed: bool
    remaining: int
    limit: int
    retry_after_seconds: int


def hash_client_ip(ip: str) -> str:
    """Hash do IP do cliente — evita persistir dado pessoal em claro."""
    return hashlib.sha256(ip.encode()).hexdigest()


class RateLimiter:
    """Contador de execuções por IP em janela horária.

    Degrada em **fail-open**: se o Redis estiver indisponível, a requisição é
    permitida e um alerta é logado. A alternativa (fail-closed) derrubaria a
    aplicação inteira por causa do cache — trade-off documentado no ADR-0004.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: aioredis.Redis | None = None

    @property
    def enabled(self) -> bool:
        """Rate limiting exige Redis; sem ele, não há contagem possível."""
        return self.settings.cache_enabled

    async def _get_client(self) -> aioredis.Redis | None:
        if not self.enabled:
            return None
        if self._client is None:
            self._client = aioredis.from_url(
                self.settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=self.settings.REDIS_CONNECT_TIMEOUT,
            )
        return self._client

    async def check(self, ip_hash: str) -> RateLimitResult:
        """Incrementa o contador do cliente e informa se a requisição é permitida."""
        limit = self.settings.RATE_LIMIT_EXECUTIONS_PER_HOUR
        client = await self._get_client()
        if client is None:
            # Sem Redis: fail-open (ver docstring da classe)
            return RateLimitResult(
                allowed=True,
                remaining=limit,
                limit=limit,
                retry_after_seconds=0,
            )

        key = f"{RATE_LIMIT_PREFIX}:{ip_hash}"
        try:
            async with client.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.ttl(key)
                count, ttl = await pipe.execute()

            if count == 1 or ttl < 0:
                # Primeira requisição da janela (ou chave sem TTL): define expiração
                await client.expire(key, WINDOW_SECONDS)
                ttl = WINDOW_SECONDS

            allowed = count <= limit
            if not allowed:
                logger.warning(
                    f"Rate limit excedido para cliente {ip_hash[:8]}… "
                    f"({count}/{limit} na janela)"
                )
            return RateLimitResult(
                allowed=allowed,
                remaining=max(limit - count, 0),
                limit=limit,
                retry_after_seconds=max(int(ttl), 1),
            )
        except Exception as e:
            logger.warning(f"Rate limiting indisponível (permitindo requisição): {e}")
            return RateLimitResult(
                allowed=True,
                remaining=limit,
                limit=limit,
                retry_after_seconds=0,
            )

    async def close(self) -> None:
        """Fecha a conexão com o Redis."""
        if self._client is not None:
            with suppress(Exception):
                await self._client.aclose()
            self._client = None
