"""Configuração do worker SAQ (ADR-0014).

Execução: `saq src.worker.settings.settings`

!!! warning "A ordem dos imports neste módulo é significativa"
    `isolate_redis_from_third_parties()` roda **antes** de importar
    `src.worker.tasks`, que alcança o CrewAI. O CrewAI lê `REDIS_URL` numa
    constante de módulo — depois do import, mudar o ambiente não tem efeito.
"""

from src.bootstrap import isolate_redis_from_third_parties

isolate_redis_from_third_parties()

# Imports abaixo do bootstrap por necessidade, não por descuido (ver docstring).
from typing import Any  # noqa: E402

from loguru import logger  # noqa: E402

from src.config import get_settings  # noqa: E402
from src.runtime import configure_llm_runtime  # noqa: E402
from src.services.queue_service import build_queue  # noqa: E402
from src.telemetry import configure_telemetry  # noqa: E402
from src.utils.logger import setup_logger  # noqa: E402
from src.worker.tasks import generate_itinerary  # noqa: E402


async def startup(ctx: dict[str, Any]) -> None:  # noqa: ARG001 - assinatura do SAQ
    """Prepara o runtime do worker (logs, LiteLLM, chaves, Langfuse, OTel)."""
    app_settings = get_settings()
    setup_logger(app_settings)
    configure_llm_runtime(app_settings)
    configure_telemetry(app_settings, service_name="voyager-worker")
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
