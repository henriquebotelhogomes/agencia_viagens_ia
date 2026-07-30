"""Configuração do worker SAQ (ADR-0014).

Execução: `saq src.worker.settings.settings`
"""

from typing import Any

from loguru import logger

from src.config import get_settings
from src.runtime import configure_llm_runtime
from src.services.queue_service import build_queue
from src.utils.logger import setup_logger
from src.worker.tasks import generate_itinerary


async def startup(ctx: dict[str, Any]) -> None:  # noqa: ARG001 - assinatura do SAQ
    """Prepara o runtime do worker (logs, LiteLLM, chaves, Langfuse)."""
    app_settings = get_settings()
    setup_logger(app_settings)
    configure_llm_runtime(app_settings)
    logger.info(
        f"Worker iniciado (env={app_settings.APP_ENV}, fila={app_settings.QUEUE_NAME})"
    )


async def shutdown(ctx: dict[str, Any]) -> None:  # noqa: ARG001 - assinatura do SAQ
    """Libera recursos do worker."""
    from src.db.base import dispose_engine

    await dispose_engine()
    logger.info("Worker finalizado.")


_app_settings = get_settings()

# Dicionário lido pelo comando `saq`
settings = {
    "queue": build_queue(_app_settings),
    "functions": [generate_itinerary],
    "concurrency": _app_settings.WORKER_CONCURRENCY,
    "startup": startup,
    "shutdown": shutdown,
}
