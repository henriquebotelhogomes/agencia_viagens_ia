"""Aplicação FastAPI (PRD D6 / ADR-0006).

Ponto de entrada da API. Toda a configuração de runtime acontece no `lifespan` —
importar este módulo não conecta em nada (invariante da Fase 0, item S1).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.errors import (
    ProblemDetail,
    http_exception_handler,
    problem_detail_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.api.routers import executions, health
from src.config import get_settings
from src.db.base import dispose_engine
from src.runtime import configure_llm_runtime
from src.services.progress_bus import ProgressBus
from src.services.queue_service import close_queue
from src.services.rate_limiter import RateLimiter
from src.utils.logger import setup_logger

DESCRIPTION = """
API de planejamento de viagens com IA multiagente.

A geração de roteiro é **assíncrona**: `POST /v1/executions` responde `202` e o
progresso é acompanhado por Server-Sent Events. Erros seguem o padrão
[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (`application/problem+json`).
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa e finaliza os recursos compartilhados da aplicação."""
    settings = get_settings()
    setup_logger(settings)
    configure_llm_runtime(settings)

    app.state.progress_bus = ProgressBus(settings)
    app.state.rate_limiter = RateLimiter(settings)
    logger.info(
        f"API iniciada (env={settings.APP_ENV}, "
        f"db={settings.database_enabled}, queue={settings.cache_enabled})"
    )

    yield

    await app.state.progress_bus.close()
    await app.state.rate_limiter.close()
    await close_queue()
    if settings.database_enabled:
        await dispose_engine()
    logger.info("API finalizada.")


def create_app() -> FastAPI:
    """Monta a aplicação FastAPI com rotas, handlers e middleware."""
    settings = get_settings()
    app = FastAPI(
        title="Voyager AI API",
        description=DESCRIPTION,
        version=health.API_VERSION,
        lifespan=lifespan,
        # Docs interativas apenas fora de produção
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url="/openapi.json",
    )

    # CORS restrito: em produção só o frontend configurado
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Idempotency-Key"],
    )

    # Erros no padrão RFC 9457
    app.add_exception_handler(ProblemDetail, problem_detail_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    app.include_router(health.router)
    app.include_router(executions.router)
    return app


app = create_app()
