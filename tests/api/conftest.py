"""Fixtures da API: app isolado com banco SQLite em memória e serviços fake.

Os testes da API não usam Postgres nem Redis reais — o objetivo é validar
contratos, validação e regras, não a infraestrutura.
"""

import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.deps import (
    client_ip_hash_dep,
    progress_bus_dep,
    rate_limiter_dep,
    session_dep,
    settings_dep,
)
from src.api.main import create_app
from src.api.schemas import ProgressEvent
from src.config import Settings
from src.db.base import Base
from src.services.rate_limiter import RateLimitResult


@dataclass
class FakeProgressBus:
    """Barramento de progresso em memória, para inspeção nos testes."""

    published: list[ProgressEvent]
    events_to_emit: list[ProgressEvent]

    async def publish(self, event: ProgressEvent) -> None:
        self.published.append(event)

    async def subscribe(self, execution_id: uuid.UUID) -> AsyncIterator[ProgressEvent]:
        for event in self.events_to_emit:
            if event.execution_id == execution_id:
                yield event

    async def close(self) -> None:
        return None


@dataclass
class FakeRateLimiter:
    """Rate limiter controlável: permite ou bloqueia conforme o teste."""

    allowed: bool = True
    limit: int = 5

    async def check(self, ip_hash: str) -> RateLimitResult:
        return RateLimitResult(
            allowed=self.allowed,
            remaining=self.limit if self.allowed else 0,
            limit=self.limit,
            retry_after_seconds=0 if self.allowed else 1800,
        )

    async def close(self) -> None:
        return None


@pytest.fixture
def api_settings() -> Settings:
    """Configuração com banco e fila habilitados (valores fake)."""
    return Settings(
        _env_file=None,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/0",
        OPENCODE_API_KEY="mock_go_key",
        OPENROUTER_API_KEY="mock_or_key",
    )


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Sessão sobre SQLite em memória, com o schema criado a partir dos modelos."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def fake_progress_bus() -> FakeProgressBus:
    return FakeProgressBus(published=[], events_to_emit=[])


@pytest.fixture
def fake_rate_limiter() -> FakeRateLimiter:
    return FakeRateLimiter()


@pytest.fixture
async def client(
    api_settings: Settings,
    db_session: AsyncSession,
    fake_progress_bus: FakeProgressBus,
    fake_rate_limiter: FakeRateLimiter,
    mocker,
) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP com todas as dependências externas substituídas."""
    # Não conecta em Redis nem executa runtime de LLM durante os testes
    mocker.patch("src.api.main.configure_llm_runtime")
    mocker.patch("src.api.main.setup_logger")
    mocker.patch("src.api.main.close_queue")
    mocker.patch("src.api.main.dispose_engine")
    mocker.patch("src.api.routers.executions.enqueue_generation")

    app = create_app()
    app.dependency_overrides[settings_dep] = lambda: api_settings
    app.dependency_overrides[session_dep] = lambda: db_session
    app.dependency_overrides[progress_bus_dep] = lambda: fake_progress_bus
    app.dependency_overrides[rate_limiter_dep] = lambda: fake_rate_limiter
    app.dependency_overrides[client_ip_hash_dep] = lambda: "hash_de_teste"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
