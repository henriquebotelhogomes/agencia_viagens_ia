"""Aplicação FastAPI (PRD D6 / ADR-0006).

Ponto de entrada da API. Toda a configuração de runtime acontece no `lifespan` —
importar este módulo não conecta em nada (invariante da Fase 0, item S1).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.errors import (
    PROBLEM_CONTENT_TYPE,
    ProblemDetail,
    http_exception_handler,
    problem_detail_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.api.routers import executions, health
from src.api.schemas import ProblemDetailResponse
from src.config import get_settings
from src.db.base import dispose_engine
from src.runtime import configure_llm_runtime
from src.services.progress_bus import ProgressBus
from src.services.queue_service import close_queue
from src.services.rate_limiter import RateLimiter
from src.telemetry import configure_telemetry
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
    configure_telemetry(settings, service_name="voyager-api", app=app)

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


def _document_problem_responses(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """Alinha a OpenAPI ao comportamento real dos handlers de erro.

    O FastAPI documenta o 422 como ``HTTPValidationError`` em
    ``application/json``, mas os handlers desta API respondem **tudo** que é
    erro no envelope RFC 9457 (``application/problem+json``). Sem este ajuste,
    os testes de contrato (schemathesis) reprovam a spec — com razão.
    """
    problem_schema = ProblemDetailResponse.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    components = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
    components["ProblemDetailResponse"] = problem_schema
    # O modelo não tem refs aninhadas; o 422 padrão do FastAPI deixa de existir
    components.pop("HTTPValidationError", None)
    components.pop("ValidationError", None)

    problem_content = {
        PROBLEM_CONTENT_TYPE: {
            "schema": {"$ref": "#/components/schemas/ProblemDetailResponse"}
        }
    }
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            # Corpo ilegível (JSON malformado) faz o Starlette responder 400 antes
            # de a validação do Pydantic rodar — é distinto do 422, que já
            # pressupõe JSON válido com campos inválidos.
            if "requestBody" in operation:
                responses.setdefault(
                    "400", {"description": "Corpo da requisição não é JSON válido"}
                )
            for status_code, response in responses.items():
                if status_code.isdigit() and int(status_code) >= 400:
                    response["content"] = problem_content
    return openapi_schema


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

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = _document_problem_responses(
            get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
        )
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app


app = create_app()
