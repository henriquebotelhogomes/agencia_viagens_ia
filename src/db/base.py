"""Camada de acesso a dados (SQLAlchemy 2.0 async).

Persistência de execuções e roteiros em PostgreSQL (PRD D8 / ADR-0008). O engine
é criado sob demanda e memoizado — importar este módulo não abre conexão.

Separação intencional: `build_engine(settings)` é pura e aceita configuração
injetada (usada em testes); `get_engine()` é a versão memoizada do processo.
Misturar as duas num único `lru_cache` quebraria, pois `Settings` não é hashable.
"""

from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.config import Settings, get_settings


class Base(DeclarativeBase):
    """Base declarativa de todos os modelos."""


def build_engine(settings: Settings | None = None) -> AsyncEngine:
    """Cria um engine async a partir da configuração informada.

    Raises:
        RuntimeError: se ``DATABASE_URL`` não estiver configurada.
    """
    resolved = settings or get_settings()
    if not resolved.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL não configurada — necessária para persistência (ADR-0008)."
        )

    options: dict[str, Any] = {
        "echo": False,
        "pool_pre_ping": True,  # evita usar conexão derrubada pelo servidor
    }
    # SQLite (usado nos testes) roda com StaticPool e rejeita esses parâmetros
    if not resolved.DATABASE_URL.startswith("sqlite"):
        options["pool_size"] = resolved.DB_POOL_SIZE
        options["max_overflow"] = resolved.DB_MAX_OVERFLOW

    return create_async_engine(resolved.DATABASE_URL, **options)


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Engine compartilhado do processo (criado no primeiro uso)."""
    return build_engine()


def build_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Cria uma fábrica de sessões para a configuração informada."""
    return async_sessionmaker(
        bind=build_engine(settings),
        expire_on_commit=False,  # permite ler atributos após o commit
        autoflush=False,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Fábrica de sessões compartilhada, vinculada ao engine do processo."""
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependência do FastAPI: fornece uma sessão por request.

    Faz rollback automático em exceção e sempre fecha a sessão.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    """Fecha o pool de conexões (chamado no shutdown da aplicação)."""
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
