"""Publicação e consumo de progresso de execução via Redis pub/sub (FR-03).

O worker publica eventos; a API os transmite ao cliente por SSE. Esse
desacoplamento evita que o worker conheça HTTP e que a API conheça a orquestração.
"""

import uuid
from collections.abc import AsyncIterator
from contextlib import suppress

import redis.asyncio as aioredis
from loguru import logger

from src.api.schemas import ProgressEvent
from src.config import Settings, get_settings
from src.db.models import ExecutionStatus

# Prefixo dos canais de progresso; um canal por execução
CHANNEL_PREFIX = "execution:progress"
# Intervalo do heartbeat do SSE, para manter a conexão viva atrás de proxies
HEARTBEAT_SECONDS = 15.0

_TERMINAL_STATUSES = frozenset(
    {
        ExecutionStatus.SUCCEEDED,
        ExecutionStatus.FAILED,
        ExecutionStatus.CANCELLED,
    }
)


def channel_for(execution_id: uuid.UUID) -> str:
    """Nome do canal pub/sub de uma execução."""
    return f"{CHANNEL_PREFIX}:{execution_id}"


class ProgressBus:
    """Canal de eventos de progresso sobre Redis pub/sub.

    Degrada graciosamente: sem Redis configurado, publicar é no-op e a assinatura
    encerra imediatamente — a execução continua, apenas sem streaming.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: aioredis.Redis | None = None

    @property
    def enabled(self) -> bool:
        """Indica se há Redis configurado para transportar os eventos."""
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

    async def publish(self, event: ProgressEvent) -> None:
        """Publica um evento de progresso. Falha de Redis não interrompe o job."""
        client = await self._get_client()
        if client is None:
            return
        try:
            await client.publish(
                channel_for(event.execution_id), event.model_dump_json()
            )
        except Exception as e:
            logger.warning(f"Falha ao publicar progresso: {e}")

    async def subscribe(self, execution_id: uuid.UUID) -> AsyncIterator[ProgressEvent]:
        """Itera sobre os eventos de uma execução até o estado terminal."""
        client = await self._get_client()
        if client is None:
            return

        pubsub = client.pubsub()
        await pubsub.subscribe(channel_for(execution_id))
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS
                )
                if message is None:
                    continue  # timeout: quem consome decide enviar heartbeat
                try:
                    event = ProgressEvent.model_validate_json(message["data"])
                except ValueError as e:
                    logger.warning(f"Evento de progresso inválido descartado: {e}")
                    continue
                yield event
                if event.status in _TERMINAL_STATUSES:
                    return
        finally:
            with suppress(Exception):
                await pubsub.unsubscribe(channel_for(execution_id))
                await pubsub.close()

    async def close(self) -> None:
        """Fecha a conexão com o Redis."""
        if self._client is not None:
            with suppress(Exception):
                await self._client.aclose()
            self._client = None
