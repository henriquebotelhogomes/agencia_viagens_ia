"""Testes de contrato da OpenAPI (schemathesis).

Geram requisições a partir do próprio schema publicado em ``/openapi.json`` e
verificam se as respostas honram o contrato: status documentados, content types
e formato dos payloads. É a garantia de que a especificação que o frontend e os
consumidores leem corresponde ao comportamento real da API.
"""

import uuid
from collections.abc import AsyncIterator, Iterator
from unittest import mock

import pytest
import schemathesis
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.api.deps import (
    client_ip_hash_dep,
    progress_bus_dep,
    rate_limiter_dep,
    session_dep,
    settings_dep,
)
from src.api.main import create_app
from src.config import Settings
from src.db.base import Base
from src.services.rate_limiter import RateLimitResult


class _AllowAllRateLimiter:
    async def check(self, ip_hash: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=True, remaining=5, limit=5, retry_after_seconds=0
        )


class _SilentProgressBus:
    """Sem eventos: o endpoint de SSE encerra imediatamente, sem pendurar."""

    async def publish(self, event: object) -> None:
        return None

    async def subscribe(self, execution_id: uuid.UUID) -> AsyncIterator[object]:
        return
        yield  # pragma: no cover - torna a função um async generator

    async def close(self) -> None:
        return None


@pytest.fixture(scope="module")
def contract_schema() -> Iterator[schemathesis.BaseSchema]:
    """App com dependências externas substituídas + schema carregado via ASGI.

    Escopo de módulo: o schemathesis busca o ``/openapi.json`` uma única vez e
    reusa o app para todos os exemplos gerados.
    """
    patches = [
        # O cliente do schemathesis executa o lifespan de verdade — nada de
        # conectar em Redis nem configurar runtime de LLM durante os testes.
        mock.patch("src.api.main.configure_llm_runtime"),
        mock.patch("src.api.main.setup_logger"),
        mock.patch("src.api.main.close_queue"),
        mock.patch("src.api.main.dispose_engine"),
        mock.patch("src.api.routers.executions.enqueue_generation"),
    ]
    for patch in patches:
        patch.start()

    api_settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        OPENCODE_API_KEY="mock_go_key",
        OPENROUTER_API_KEY="mock_or_key",
    )

    # A factory nasce dentro do loop do app (aiosqlite prende a conexão ao
    # loop em que foi criada; criá-la aqui fora quebraria nas requisições).
    state: dict[str, async_sessionmaker | None] = {"factory": None}

    async def override_session() -> AsyncIterator[object]:
        if state["factory"] is None:
            engine = create_async_engine("sqlite+aiosqlite:///:memory:")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            state["factory"] = async_sessionmaker(bind=engine, expire_on_commit=False)
        async with state["factory"]() as session:
            yield session

    app = create_app()
    app.dependency_overrides[settings_dep] = lambda: api_settings
    app.dependency_overrides[session_dep] = override_session
    app.dependency_overrides[progress_bus_dep] = _SilentProgressBus
    app.dependency_overrides[rate_limiter_dep] = _AllowAllRateLimiter
    app.dependency_overrides[client_ip_hash_dep] = lambda: "hash_de_contrato"

    yield schemathesis.openapi.from_asgi("/openapi.json", app)

    for patch in patches:
        patch.stop()


schema = schemathesis.pytest.from_fixture("contract_schema")


@schema.parametrize()
@hypothesis_settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
def test_api_honra_o_contrato_openapi(case: schemathesis.Case) -> None:
    """Toda resposta deve estar documentada: status, content type e schema."""
    case.call_and_validate()
