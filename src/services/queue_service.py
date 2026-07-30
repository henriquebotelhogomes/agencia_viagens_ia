"""Enfileiramento de jobs de geração de roteiro (ADR-0014).

A API apenas enfileira; o worker executa. Este módulo isola a biblioteca de fila
(SAQ) do resto do código — trocá-la exige mudar apenas aqui.
"""

import uuid
from contextlib import suppress
from functools import lru_cache

from loguru import logger
from saq import Queue

from src.config import Settings, get_settings

# Nome da task registrada no worker
GENERATE_ITINERARY_TASK = "generate_itinerary"


def build_queue(settings: Settings | None = None) -> Queue:
    """Cria a fila SAQ a partir da ``REDIS_URL``.

    Raises:
        RuntimeError: se ``REDIS_URL`` não estiver configurada.
    """
    resolved = settings or get_settings()
    if not resolved.cache_enabled:
        raise RuntimeError(
            "REDIS_URL não configurada — necessária para a fila de jobs (ADR-0014)."
        )
    return Queue.from_url(resolved.REDIS_URL, name=resolved.QUEUE_NAME)


@lru_cache(maxsize=1)
def get_queue() -> Queue:
    """Retorna a fila da aplicação (memoizada)."""
    return build_queue()


async def enqueue_generation(
    execution_id: uuid.UUID, queue: Queue | None = None
) -> str:
    """Enfileira a geração de um roteiro.

    Args:
        execution_id: identificador da execução já persistida.
        queue: fila a usar (injeta em testes).

    Returns:
        Chave do job na fila.
    """
    settings = get_settings()
    resolved_queue = queue or get_queue()
    job = await resolved_queue.enqueue(
        GENERATE_ITINERARY_TASK,
        execution_id=str(execution_id),
        timeout=settings.JOB_TIMEOUT_SECONDS,
    )
    if job is None:  # pragma: no cover - SAQ retorna None em job duplicado
        logger.warning(f"Job já enfileirado para a execução {execution_id}.")
        return ""
    logger.info(f"Execução {execution_id} enfileirada (job {job.key}).")
    return str(job.key)


async def close_queue() -> None:
    """Fecha a conexão da fila (shutdown da aplicação)."""
    if get_queue.cache_info().currsize:
        with suppress(Exception):
            await get_queue().disconnect()
    get_queue.cache_clear()
